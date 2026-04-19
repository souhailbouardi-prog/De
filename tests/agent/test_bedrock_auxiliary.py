"""Tests for BedrockAuxiliaryClient and aws_sdk auth_type in resolve_provider_client.

Covers:
  - BedrockAuxiliaryClient wrapper creates correct client structure
  - _BedrockCompletionsAdapter delegates to bedrock_adapter.call_converse
  - AsyncBedrockAuxiliaryClient wraps sync adapter via asyncio.to_thread
  - resolve_provider_client handles aws_sdk auth_type
  - Region resolution priority: env var > explicit base_url > default
  - _to_async_client recognizes BedrockAuxiliaryClient
  - Graceful fallback when AWS credentials are unavailable
"""

import asyncio
import os
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

import pytest

from agent.auxiliary_client import (
    BedrockAuxiliaryClient,
    AsyncBedrockAuxiliaryClient,
    _BedrockCompletionsAdapter,
    resolve_provider_client,
    _to_async_client,
)


_FAKE_RESPONSE = SimpleNamespace(
    choices=[SimpleNamespace(message=SimpleNamespace(content="OK"))],
    model="test-model",
    usage=SimpleNamespace(prompt_tokens=10, completion_tokens=5),
)


# ---------------------------------------------------------------------------
# BedrockAuxiliaryClient structure
# ---------------------------------------------------------------------------


class TestBedrockAuxiliaryClient:
    """BedrockAuxiliaryClient exposes the standard OpenAI-compatible interface."""

    def test_has_chat_completions_interface(self):
        client = BedrockAuxiliaryClient("us-east-1", "some-model")
        assert hasattr(client, "chat")
        assert hasattr(client.chat, "completions")
        assert hasattr(client.chat.completions, "create")

    def test_exposes_api_key_and_base_url(self):
        client = BedrockAuxiliaryClient("ap-southeast-1", "model-id")
        assert client.api_key == "aws-sdk"
        assert "ap-southeast-1" in client.base_url

    def test_close_is_noop(self):
        client = BedrockAuxiliaryClient("us-east-1", "m")
        client.close()  # should not raise


# ---------------------------------------------------------------------------
# _BedrockCompletionsAdapter
# ---------------------------------------------------------------------------


class TestBedrockCompletionsAdapter:
    """Adapter translates chat.completions.create() kwargs to Bedrock Converse."""

    @patch("agent.bedrock_adapter.call_converse")
    def test_delegates_to_call_converse(self, mock_converse):
        mock_converse.return_value = _FAKE_RESPONSE
        adapter = _BedrockCompletionsAdapter("ap-southeast-1", "default-model")
        result = adapter.create(
            model="explicit-model",
            messages=[{"role": "user", "content": "hi"}],
            max_tokens=100,
            temperature=0.5,
        )
        mock_converse.assert_called_once_with(
            region="ap-southeast-1",
            model="explicit-model",
            messages=[{"role": "user", "content": "hi"}],
            max_tokens=100,
            temperature=0.5,
        )
        assert result.choices[0].message.content == "OK"

    @patch("agent.bedrock_adapter.call_converse")
    def test_uses_default_model_when_none(self, mock_converse):
        mock_converse.return_value = _FAKE_RESPONSE
        adapter = _BedrockCompletionsAdapter("us-east-1", "my-default")
        adapter.create(messages=[{"role": "user", "content": "hi"}])
        assert mock_converse.call_args.kwargs["model"] == "my-default"

    @patch("agent.bedrock_adapter.call_converse")
    def test_max_completion_tokens_fallback(self, mock_converse):
        mock_converse.return_value = _FAKE_RESPONSE
        adapter = _BedrockCompletionsAdapter("us-east-1", "m")
        adapter.create(messages=[], max_completion_tokens=2048)
        assert mock_converse.call_args.kwargs["max_tokens"] == 2048


# ---------------------------------------------------------------------------
# AsyncBedrockAuxiliaryClient
# ---------------------------------------------------------------------------


class TestAsyncBedrockAuxiliaryClient:
    """Async wrapper delegates to sync adapter via asyncio.to_thread."""

    def test_has_async_interface(self):
        sync = BedrockAuxiliaryClient("us-east-1", "m")
        async_client = AsyncBedrockAuxiliaryClient(sync)
        assert hasattr(async_client, "chat")
        assert hasattr(async_client.chat, "completions")
        assert hasattr(async_client.chat.completions, "create")

    def test_preserves_api_key_and_base_url(self):
        sync = BedrockAuxiliaryClient("eu-west-1", "m")
        async_client = AsyncBedrockAuxiliaryClient(sync)
        assert async_client.api_key == "aws-sdk"
        assert "eu-west-1" in async_client.base_url

    @patch("agent.bedrock_adapter.call_converse", return_value=_FAKE_RESPONSE)
    def test_async_create_calls_sync(self, _mock):
        sync = BedrockAuxiliaryClient("us-east-1", "m")
        async_client = AsyncBedrockAuxiliaryClient(sync)
        result = asyncio.get_event_loop().run_until_complete(
            async_client.chat.completions.create(
                model="m", messages=[{"role": "user", "content": "hi"}]
            )
        )
        assert result.choices[0].message.content == "OK"


# ---------------------------------------------------------------------------
# _to_async_client integration
# ---------------------------------------------------------------------------


class TestToAsyncClientBedrock:
    """_to_async_client recognizes BedrockAuxiliaryClient."""

    def test_returns_async_bedrock_wrapper(self):
        sync = BedrockAuxiliaryClient("us-east-1", "m")
        async_client, model = _to_async_client(sync, "my-model")
        assert isinstance(async_client, AsyncBedrockAuxiliaryClient)
        assert model == "my-model"


# ---------------------------------------------------------------------------
# resolve_provider_client with aws_sdk auth_type
# ---------------------------------------------------------------------------


class TestResolveProviderClientBedrock:
    """resolve_provider_client handles the bedrock provider (aws_sdk auth)."""

    @patch("agent.bedrock_adapter.has_aws_credentials", return_value=True)
    def test_returns_bedrock_client_when_creds_available(self, _mock, monkeypatch):
        monkeypatch.setenv("AWS_DEFAULT_REGION", "ap-southeast-1")
        client, model = resolve_provider_client(
            "bedrock", "apac.anthropic.claude-sonnet-4-20250514-v1:0"
        )
        assert isinstance(client, BedrockAuxiliaryClient)
        assert "ap-southeast-1" in client.base_url
        assert model == "apac.anthropic.claude-sonnet-4-20250514-v1:0"

    @patch("agent.bedrock_adapter.has_aws_credentials", return_value=False)
    def test_returns_none_when_no_creds(self, _mock):
        client, model = resolve_provider_client("bedrock", "some-model")
        assert client is None
        assert model is None

    @patch("agent.bedrock_adapter.has_aws_credentials", return_value=True)
    def test_region_from_env_var(self, _mock, monkeypatch):
        monkeypatch.setenv("AWS_DEFAULT_REGION", "eu-central-1")
        client, _ = resolve_provider_client("bedrock", "m")
        assert "eu-central-1" in client.base_url

    @patch("agent.bedrock_adapter.has_aws_credentials", return_value=True)
    def test_region_from_explicit_base_url(self, _mock, monkeypatch):
        monkeypatch.delenv("AWS_DEFAULT_REGION", raising=False)
        monkeypatch.delenv("AWS_REGION", raising=False)
        client, _ = resolve_provider_client(
            "bedrock", "m",
            explicit_base_url="https://bedrock-runtime.us-west-2.amazonaws.com",
        )
        assert "us-west-2" in client.base_url

    @patch("agent.bedrock_adapter.has_aws_credentials", return_value=True)
    def test_region_defaults_to_us_east_1(self, _mock, monkeypatch):
        monkeypatch.delenv("AWS_DEFAULT_REGION", raising=False)
        monkeypatch.delenv("AWS_REGION", raising=False)
        client, _ = resolve_provider_client("bedrock", "m")
        assert "us-east-1" in client.base_url

    @patch("agent.bedrock_adapter.has_aws_credentials", return_value=True)
    def test_default_model_when_none_provided(self, _mock, monkeypatch):
        monkeypatch.setenv("AWS_DEFAULT_REGION", "us-east-1")
        _, model = resolve_provider_client("bedrock", None)
        assert model is not None
        assert "claude" in model.lower() or "anthropic" in model.lower()

    @patch("agent.bedrock_adapter.has_aws_credentials", return_value=True)
    def test_async_mode_returns_async_client(self, _mock, monkeypatch):
        monkeypatch.setenv("AWS_DEFAULT_REGION", "us-east-1")
        client, model = resolve_provider_client("bedrock", "m", async_mode=True)
        assert isinstance(client, AsyncBedrockAuxiliaryClient)

    @patch("agent.bedrock_adapter.has_aws_credentials", side_effect=ImportError("no boto3"))
    def test_graceful_on_import_error(self, _mock):
        client, model = resolve_provider_client("bedrock", "m")
        assert client is None
