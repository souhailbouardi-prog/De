"""Tests for _preprocess_message_images in the API server adapter.

The preprocessor converts OpenAI multipart ``image_url`` content into text
descriptions via the auxiliary vision tool, so images work end-to-end through
any provider backend (the agent pipeline itself is text-only).
"""

import base64
import json
import sys
from unittest.mock import patch

import pytest

from gateway.platforms.api_server import (
    _is_safe_image_url,
    _materialize_data_url,
    _preprocess_message_images,
    _sniff_image_mime,
    _split_content_parts,
)


# ── Helpers ──────────────────────────────────────────────────────────────

_TINY_PNG_BYTES = bytes.fromhex(
    # 1x1 solid-black PNG, smallest valid PNG file.
    "89504e470d0a1a0a0000000d49484452000000010000000108060000001f15c489"
    "0000000d49444154789c626001000000050001aa3e8d610000000049454e44ae426082"
)


def _tiny_png_data_url() -> str:
    return "data:image/png;base64," + base64.b64encode(_TINY_PNG_BYTES).decode()


async def _ok_vision(image_url, user_prompt, **_kw):
    return json.dumps({"success": True, "analysis": "a tiny black square"})


async def _failing_vision(image_url, user_prompt, **_kw):
    return json.dumps({"success": False, "analysis": "vision backend unreachable"})


async def _raising_vision(image_url, user_prompt, **_kw):
    raise RuntimeError("boom")


def _install_vision_stub(monkeypatch, impl):
    """Register a stub ``tools.vision_tools.vision_analyze_tool``.

    The preprocessor imports the tool lazily inside the function body, so we
    patch ``sys.modules`` rather than the caller's namespace.
    """
    stub = type(sys)("tools.vision_tools")
    stub.vision_analyze_tool = impl  # type: ignore[attr-defined]
    monkeypatch.setitem(sys.modules, "tools.vision_tools", stub)


def _force_allow_safe_url(monkeypatch):
    """Make ``_is_safe_image_url`` treat any http(s) URL as safe.

    Bypasses the real SSRF filter's network-dependent DNS checks so tests
    don't flake on developer boxes where DNS hijacking / Stash fake-ip
    resolves ``example.com`` to a private range.
    """
    import tools.url_safety as _url_safety
    monkeypatch.setattr(_url_safety, "is_safe_url", lambda _url: True)


# ── _split_content_parts ─────────────────────────────────────────────────


class TestSplitContentParts:
    def test_separates_text_and_images(self):
        text, urls = _split_content_parts([
            {"type": "text", "text": "hello"},
            {"type": "image_url", "image_url": {"url": "https://example/a.png"}},
            {"type": "input_text", "text": " world"},
            {"type": "image_url", "image_url": {"url": "https://example/b.png"}},
        ])
        assert text == ["hello", "world"]
        assert urls == ["https://example/a.png", "https://example/b.png"]

    def test_image_url_string_variant(self):
        _, urls = _split_content_parts([
            {"type": "image_url", "image_url": "https://example/c.png"},
        ])
        assert urls == ["https://example/c.png"]

    def test_plain_string_part_is_text(self):
        text, urls = _split_content_parts(["standalone string", {"type": "text", "text": "dict"}])
        assert text == ["standalone string", "dict"]
        assert urls == []

    def test_unknown_type_ignored(self):
        text, urls = _split_content_parts([{"type": "something_weird", "foo": "bar"}])
        assert text == []
        assert urls == []


# ── _materialize_data_url ────────────────────────────────────────────────


class TestMaterializeDataUrl:
    def test_non_data_url_passes_through(self):
        path, cleanup = _materialize_data_url("https://example.com/img.png")
        assert path == "https://example.com/img.png"
        assert cleanup is None

    def test_data_url_written_to_tempfile(self):
        url = _tiny_png_data_url()
        path, cleanup = _materialize_data_url(url)
        try:
            assert cleanup is not None
            assert cleanup.exists()
            assert cleanup.suffix == ".png"
            assert cleanup.read_bytes() == _TINY_PNG_BYTES
            assert path == str(cleanup)
        finally:
            if cleanup is not None and cleanup.exists():
                cleanup.unlink()

    def test_payload_without_image_magic_is_rejected(self):
        # Attacker-supplied Content-Type must NOT be trusted — sniff bytes.
        url = "data:image/png;base64," + base64.b64encode(b"not an image").decode()
        with pytest.raises(ValueError, match="not a recognized image format"):
            _materialize_data_url(url)

    def test_invalid_base64_rejected(self):
        url = "data:image/png;base64,%%%not base64%%%"
        with pytest.raises(ValueError, match="invalid base64"):
            _materialize_data_url(url)

    def test_oversize_payload_rejected(self):
        # Synthetic 20 MiB "image" (well past _MAX_IMAGE_BYTES = 15 MiB).
        from gateway.platforms.api_server import _MAX_IMAGE_BYTES
        big = b"\x89PNG\r\n\x1a\n" + b"\x00" * (_MAX_IMAGE_BYTES + 1)
        url = "data:image/png;base64," + base64.b64encode(big).decode()
        with pytest.raises(ValueError, match="per-image limit"):
            _materialize_data_url(url)

    def test_suffix_reflects_sniffed_mime_not_claim(self):
        # Claim JPEG but actually a PNG — suffix should match sniff, not claim.
        url = "data:image/jpeg;base64," + base64.b64encode(_TINY_PNG_BYTES).decode()
        path, cleanup = _materialize_data_url(url)
        try:
            assert cleanup is not None
            assert cleanup.suffix == ".png"
        finally:
            if cleanup is not None and cleanup.exists():
                cleanup.unlink()


class TestSniffImageMime:
    def test_png(self):
        assert _sniff_image_mime(_TINY_PNG_BYTES) == "image/png"

    def test_jpeg(self):
        assert _sniff_image_mime(b"\xff\xd8\xff\xe0foo") == "image/jpeg"

    def test_gif(self):
        assert _sniff_image_mime(b"GIF89a" + b"\x00" * 16) == "image/gif"

    def test_webp(self):
        assert _sniff_image_mime(b"RIFF\x00\x00\x00\x00WEBPfoo") == "image/webp"

    def test_arbitrary_bytes_rejected(self):
        assert _sniff_image_mime(b"plain text not an image") is None
        assert _sniff_image_mime(b"") is None


class TestIsSafeImageUrl:
    def test_data_url_allowed(self):
        assert _is_safe_image_url("data:image/png;base64,AAAA") is True

    def test_https_allowed(self, monkeypatch):
        _force_allow_safe_url(monkeypatch)
        assert _is_safe_image_url("https://example.com/img.png") is True

    @pytest.mark.parametrize("scheme", ["file://", "ftp://", "gopher://", "javascript:", "ldap://"])
    def test_non_http_schemes_rejected(self, scheme):
        assert _is_safe_image_url(scheme + "whatever/path") is False

    def test_empty_or_non_string(self):
        assert _is_safe_image_url("") is False
        assert _is_safe_image_url(None) is False  # type: ignore[arg-type]
        assert _is_safe_image_url(123) is False  # type: ignore[arg-type]

    def test_fails_closed_when_url_safety_module_missing(self, monkeypatch):
        # If the SSRF guard import fails, don't fall through to unchecked I/O.
        import builtins
        real_import = builtins.__import__

        def fake_import(name, *a, **kw):
            if name == "tools.url_safety":
                raise ImportError("simulated")
            return real_import(name, *a, **kw)

        monkeypatch.setattr(builtins, "__import__", fake_import)
        assert _is_safe_image_url("https://example.com/x.png") is False

    def test_ssrf_target_rejected(self, monkeypatch):
        # Mock is_safe_url → False to simulate a private-IP / metadata URL.
        stub = sys.modules.setdefault("tools.url_safety", type(sys)("tools.url_safety"))
        monkeypatch.setattr(stub, "is_safe_url", lambda _url: False, raising=False)
        assert _is_safe_image_url("http://169.254.169.254/latest/meta-data/") is False


# ── _preprocess_message_images ───────────────────────────────────────────


class TestPreprocessMessageImages:
    @pytest.mark.asyncio
    async def test_no_images_leaves_messages_untouched(self, monkeypatch):
        _install_vision_stub(monkeypatch, _ok_vision)
        messages = [{"role": "user", "content": "just text"}]
        await _preprocess_message_images(messages)
        assert messages == [{"role": "user", "content": "just text"}]

    @pytest.mark.asyncio
    async def test_multipart_without_image_is_untouched(self, monkeypatch):
        _install_vision_stub(monkeypatch, _ok_vision)
        messages = [{
            "role": "user",
            "content": [{"type": "text", "text": "hi"}],
        }]
        await _preprocess_message_images(messages)
        # We only flatten when images are present; text-only multi-part is left
        # for _normalize_chat_content to handle.
        assert messages[0]["content"] == [{"type": "text", "text": "hi"}]

    @pytest.mark.asyncio
    async def test_image_with_text_becomes_enriched_string(self, monkeypatch):
        _install_vision_stub(monkeypatch, _ok_vision)
        messages = [{
            "role": "user",
            "content": [
                {"type": "text", "text": "what's this?"},
                {"type": "image_url", "image_url": {"url": _tiny_png_data_url()}},
            ],
        }]
        await _preprocess_message_images(messages)
        content = messages[0]["content"]
        assert isinstance(content, str)
        assert "a tiny black square" in content
        assert "what's this?" in content
        # Description prefixes the user's text.
        assert content.index("a tiny black square") < content.index("what's this?")

    @pytest.mark.asyncio
    async def test_image_without_text(self, monkeypatch):
        _install_vision_stub(monkeypatch, _ok_vision)
        messages = [{
            "role": "user",
            "content": [
                {"type": "image_url", "image_url": {"url": _tiny_png_data_url()}},
            ],
        }]
        await _preprocess_message_images(messages)
        assert messages[0]["content"] == (
            "[The user attached an image. Here's what it contains:\n"
            "a tiny black square]"
        )

    @pytest.mark.asyncio
    async def test_multiple_images_concatenated(self, monkeypatch):
        _install_vision_stub(monkeypatch, _ok_vision)
        messages = [{
            "role": "user",
            "content": [
                {"type": "image_url", "image_url": {"url": _tiny_png_data_url()}},
                {"type": "image_url", "image_url": {"url": _tiny_png_data_url()}},
                {"type": "text", "text": "compare"},
            ],
        }]
        await _preprocess_message_images(messages)
        content = messages[0]["content"]
        # Both descriptions appear, separated from user text.
        assert content.count("a tiny black square") == 2
        assert content.endswith("compare")

    @pytest.mark.asyncio
    async def test_vision_tool_failure_produces_neutral_note(self, monkeypatch, caplog):
        _force_allow_safe_url(monkeypatch)
        _install_vision_stub(monkeypatch, _failing_vision)
        messages = [{
            "role": "user",
            "content": [
                {"type": "text", "text": "look"},
                {"type": "image_url", "image_url": {"url": "https://example.com/x.png"}},
            ],
        }]
        with caplog.at_level("WARNING"):
            await _preprocess_message_images(messages)
        content = messages[0]["content"]
        assert isinstance(content, str)
        # User-facing message is neutral; upstream detail must not leak.
        assert "could not be processed" in content
        assert "vision backend unreachable" not in content
        assert "look" in content
        # Operator-facing log DOES carry the detail.
        assert any(
            "vision backend unreachable" in r.getMessage() for r in caplog.records
        )

    @pytest.mark.asyncio
    async def test_vision_tool_exception_does_not_leak(self, monkeypatch, caplog):
        _force_allow_safe_url(monkeypatch)
        _install_vision_stub(monkeypatch, _raising_vision)
        messages = [{
            "role": "user",
            "content": [
                {"type": "image_url", "image_url": {"url": "https://example.com/x.png"}},
            ],
        }]
        with caplog.at_level("WARNING"):
            await _preprocess_message_images(messages)
        content = messages[0]["content"]
        # Exception repr ("boom", the RuntimeError) is logged but NOT exposed.
        assert "boom" not in content
        assert "could not be processed" in content
        assert any("boom" in r.getMessage() for r in caplog.records)

    @pytest.mark.asyncio
    async def test_unsafe_url_is_rejected_without_calling_vision(self, monkeypatch, caplog):
        """file:// and other non-http(s) schemes bypass the vision tool entirely."""
        calls = []

        async def spy_vision(image_url, user_prompt, **_kw):
            calls.append(image_url)
            return json.dumps({"success": True, "analysis": "leaked"})

        _install_vision_stub(monkeypatch, spy_vision)
        messages = [{
            "role": "user",
            "content": [
                {"type": "image_url", "image_url": {"url": "file:///etc/passwd"}},
                {"type": "text", "text": "what's in my file?"},
            ],
        }]
        with caplog.at_level("WARNING"):
            await _preprocess_message_images(messages)
        assert calls == []  # vision tool never invoked for the unsafe URL
        content = messages[0]["content"]
        assert "could not be processed" in content
        assert "passwd" not in content
        assert "what's in my file?" in content
        assert any(
            "rejecting unsafe image url" in r.getMessage() for r in caplog.records
        )

    @pytest.mark.asyncio
    async def test_data_url_tempfile_cleaned_up(self, monkeypatch):
        seen_paths = []

        async def capture_vision(image_url, user_prompt, **_kw):
            seen_paths.append(image_url)
            return json.dumps({"success": True, "analysis": "ok"})

        _install_vision_stub(monkeypatch, capture_vision)
        messages = [{
            "role": "user",
            "content": [
                {"type": "image_url", "image_url": {"url": _tiny_png_data_url()}},
            ],
        }]
        await _preprocess_message_images(messages)
        assert len(seen_paths) == 1
        # The tempfile the tool received must have been cleaned up after use.
        from pathlib import Path
        assert not Path(seen_paths[0]).exists()

    @pytest.mark.asyncio
    async def test_missing_vision_tool_does_not_crash(self, monkeypatch):
        # Simulate ``from tools.vision_tools import vision_analyze_tool``
        # raising ImportError by blocking the import.
        import builtins
        real_import = builtins.__import__

        def fake_import(name, *a, **kw):
            if name == "tools.vision_tools":
                raise ImportError("simulated missing")
            return real_import(name, *a, **kw)

        monkeypatch.setattr(builtins, "__import__", fake_import)
        messages = [{
            "role": "user",
            "content": [
                {"type": "text", "text": "still here"},
                {"type": "image_url", "image_url": {"url": "https://x/y.png"}},
            ],
        }]
        await _preprocess_message_images(messages)
        # Message content is left as-is so downstream normalization handles it.
        assert isinstance(messages[0]["content"], list)

    @pytest.mark.asyncio
    async def test_non_user_messages_also_processed(self, monkeypatch):
        """Processor walks every message, not just user ones."""
        _install_vision_stub(monkeypatch, _ok_vision)
        messages = [
            {"role": "assistant", "content": [
                {"type": "image_url", "image_url": {"url": _tiny_png_data_url()}},
            ]},
        ]
        await _preprocess_message_images(messages)
        assert "a tiny black square" in messages[0]["content"]
