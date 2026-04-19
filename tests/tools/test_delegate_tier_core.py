#!/usr/bin/env python3

import json
import threading
import unittest
from unittest.mock import MagicMock, patch

from tools.delegate_tool import DELEGATE_TASK_SCHEMA, _build_child_agent, delegate_task


def _make_mock_parent(depth=0):
    parent = MagicMock()
    parent.base_url = "https://openrouter.ai/api/v1"
    parent.api_key = "parent-key"
    parent.provider = "openrouter"
    parent.api_mode = "chat_completions"
    parent.model = "anthropic/claude-sonnet-4"
    parent.platform = "cli"
    parent.providers_allowed = None
    parent.providers_ignored = None
    parent.providers_order = None
    parent.provider_sort = None
    parent._session_db = None
    parent._delegate_depth = depth
    parent._active_children = []
    parent._active_children_lock = threading.Lock()
    parent._print_fn = None
    parent.tool_progress_callback = None
    parent.thinking_callback = None
    parent.max_tokens = None
    parent.reasoning_config = {"enabled": True, "effort": "xhigh"}
    return parent


class TestDelegateTierProfiles(unittest.TestCase):
    def test_schema_exposes_explicit_tiers_but_not_auto(self):
        props = DELEGATE_TASK_SCHEMA["parameters"]["properties"]
        top_enum = props["tier"]["enum"]
        task_enum = props["tasks"]["items"]["properties"]["tier"]["enum"]

        for expected in ["light", "heavy", "review", "planning", "research"]:
            self.assertIn(expected, top_enum)
            self.assertIn(expected, task_enum)
        self.assertNotIn("auto", top_enum)
        self.assertNotIn("auto", task_enum)

    def test_resolve_tier_config_merges_default_and_applies_reasoning_floor(self):
        from tools.delegate_tool import resolve_tier_config

        cfg = {
            "model": "gpt-5.4-mini",
            "reasoning_effort": "low",
            "max_iterations": 25,
            "default_tier": "review",
            "tiers": {
                "review": {
                    "model": "gpt-5.4",
                    "reasoning_effort": "low",
                    "max_iterations": 60,
                }
            },
        }

        result = resolve_tier_config(cfg)
        self.assertEqual(result["model"], "gpt-5.4")
        self.assertEqual(result["max_iterations"], 60)
        self.assertEqual(result["reasoning_effort"], "high")
        self.assertNotIn("tiers", result)
        self.assertNotIn("default_tier", result)

    def test_resolve_tier_config_unknown_explicit_and_default_fall_back_cleanly(self):
        from tools.delegate_tool import resolve_tier_config

        cfg = {
            "model": "gpt-5.4-mini",
            "reasoning_effort": "low",
            "default_tier": "bogus",
            "tiers": {"review": {"model": "gpt-5.4", "reasoning_effort": "high"}},
        }

        with self.assertLogs("tools.delegate_tool", level="WARNING") as default_logs:
            default_result = resolve_tier_config(cfg)
        self.assertEqual(default_result["model"], "gpt-5.4-mini")
        self.assertNotIn("tiers", default_result)
        self.assertTrue(any("unknown default_tier" in msg for msg in default_logs.output))

        with self.assertLogs("tools.delegate_tool", level="WARNING") as explicit_logs:
            explicit_result = resolve_tier_config(cfg, tier="unknown")
        self.assertEqual(explicit_result["model"], "gpt-5.4-mini")
        self.assertTrue(any("unknown delegation tier" in msg for msg in explicit_logs.output))

    @patch("tools.delegate_tool._load_config")
    @patch("run_agent.AIAgent")
    def test_build_child_agent_override_reasoning_effort_beats_delegation_config(self, MockAgent, mock_cfg):
        mock_cfg.return_value = {"reasoning_effort": "low"}
        MockAgent.return_value = MagicMock()
        parent = _make_mock_parent()

        _build_child_agent(
            task_index=0,
            goal="review the patch",
            context=None,
            toolsets=None,
            model=None,
            max_iterations=50,
        task_count=1,
            parent_agent=parent,
            override_reasoning_effort="high",
        )

        call_kwargs = MockAgent.call_args[1]
        self.assertEqual(call_kwargs["reasoning_config"], {"enabled": True, "effort": "high"})

    @patch("tools.delegate_tool._run_single_child")
    @patch("tools.delegate_tool._build_child_agent")
    @patch("tools.delegate_tool._resolve_delegation_credentials")
    @patch("tools.delegate_tool._load_config")
    @patch("tools.delegate_tool._get_max_concurrent_children")
    def test_batch_per_task_tier_overrides_top_level_tier(
        self,
        mock_max_children,
        mock_load_config,
        mock_resolve_creds,
        mock_build_child,
        mock_run_child,
    ):
        mock_max_children.return_value = 3
        mock_load_config.return_value = {
            "model": "gpt-5.4-mini",
            "reasoning_effort": "low",
            "max_iterations": 25,
            "tiers": {
                "heavy": {"reasoning_effort": "medium", "max_iterations": 50},
                "light": {"reasoning_effort": "low", "max_iterations": 10},
                "review": {"reasoning_effort": "low", "max_iterations": 60},
            },
        }
        mock_resolve_creds.return_value = {
            "model": "gpt-5.4-mini",
            "provider": None,
            "base_url": None,
            "api_key": None,
            "api_mode": None,
        }
        mock_build_child.side_effect = [MagicMock(), MagicMock()]
        mock_run_child.side_effect = [
            {"task_index": 0, "status": "completed", "summary": "light done", "api_calls": 1, "duration_seconds": 0.1},
            {"task_index": 1, "status": "completed", "summary": "review done", "api_calls": 1, "duration_seconds": 0.1},
        ]
        parent = _make_mock_parent()

        result = json.loads(
            delegate_task(
                tier="heavy",
                tasks=[
                    {"goal": "list the files", "tier": "light"},
                    {"goal": "review this diff", "tier": "review"},
                ],
                parent_agent=parent,
            )
        )

        self.assertEqual(len(result["results"]), 2)
        first_kwargs = mock_build_child.call_args_list[0].kwargs
        second_kwargs = mock_build_child.call_args_list[1].kwargs
        self.assertEqual(first_kwargs["max_iterations"], 10)
        self.assertEqual(first_kwargs["override_reasoning_effort"], "low")
        self.assertEqual(second_kwargs["max_iterations"], 60)
        self.assertEqual(second_kwargs["override_reasoning_effort"], "high")

    def test_heuristic_auto_router_only_uses_supported_real_tiers(self):
        from tools.delegate_tool import _infer_delegate_tier, _resolve_effective_tier

        self.assertEqual(_infer_delegate_tier("please review this patch", "", ["file"], {}), "review")
        self.assertEqual(_infer_delegate_tier("plan the architecture", "", ["file"], {}), "planning")
        self.assertEqual(_infer_delegate_tier("research the options", "", ["web"], {}), "research")
        self.assertEqual(_infer_delegate_tier("count the files", "", ["file"], {}), "light")
        self.assertIsNone(_infer_delegate_tier("implement", "", ["terminal", "file"], {}))

        cfg = {"auto_tier_selection": True, "default_tier": "heavy"}
        self.assertEqual(_resolve_effective_tier(None, "review this patch", "", ["file"], cfg), "review")
        self.assertEqual(_resolve_effective_tier("planning", "review this patch", "", ["file"], cfg), "planning")
        self.assertIsNone(_resolve_effective_tier(None, "implement", "", ["terminal", "file"], {"auto_tier_selection": False}))

    @patch("tools.delegate_tool._run_single_child")
    @patch("tools.delegate_tool._build_child_agent")
    @patch("tools.delegate_tool._resolve_delegation_credentials")
    @patch("tools.delegate_tool._load_config")
    @patch("tools.delegate_tool._get_max_concurrent_children")
    def test_single_task_uses_heuristic_tier_when_enabled_and_no_explicit_tier(
        self,
        mock_max_children,
        mock_load_config,
        mock_resolve_creds,
        mock_build_child,
        mock_run_child,
    ):
        mock_max_children.return_value = 3
        mock_load_config.return_value = {
            "model": "gpt-5.4-mini",
            "max_iterations": 25,
            "auto_tier_selection": True,
            "default_tier": "heavy",
            "tiers": {
                "review": {"reasoning_effort": "low", "max_iterations": 60},
                "heavy": {"reasoning_effort": "medium", "max_iterations": 50},
            },
        }
        mock_resolve_creds.return_value = {
            "model": "gpt-5.4-mini",
            "provider": None,
            "base_url": None,
            "api_key": None,
            "api_mode": None,
        }
        mock_build_child.return_value = MagicMock()
        mock_run_child.return_value = {"task_index": 0, "status": "completed", "summary": "ok", "api_calls": 1, "duration_seconds": 0.1}

        result = json.loads(delegate_task(goal="review this patch", parent_agent=_make_mock_parent()))

        self.assertEqual(result["results"][0]["status"], "completed")
        kwargs = mock_build_child.call_args.kwargs
        self.assertEqual(kwargs["max_iterations"], 60)
        self.assertEqual(kwargs["override_reasoning_effort"], "high")

    @patch("tools.delegate_tool._run_single_child")
    @patch("tools.delegate_tool._build_child_agent")
    @patch("tools.delegate_tool._resolve_delegation_credentials")
    @patch("tools.delegate_tool._load_config")
    @patch("tools.delegate_tool._get_max_concurrent_children")
    def test_explicit_tier_bypasses_heuristic(
        self,
        mock_max_children,
        mock_load_config,
        mock_resolve_creds,
        mock_build_child,
        mock_run_child,
    ):
        mock_max_children.return_value = 3
        mock_load_config.return_value = {
            "model": "gpt-5.4-mini",
            "max_iterations": 25,
            "auto_tier_selection": True,
            "tiers": {
                "planning": {"reasoning_effort": "low", "max_iterations": 40},
                "review": {"reasoning_effort": "low", "max_iterations": 60},
            },
        }
        mock_resolve_creds.return_value = {
            "model": "gpt-5.4-mini",
            "provider": None,
            "base_url": None,
            "api_key": None,
            "api_mode": None,
        }
        mock_build_child.return_value = MagicMock()
        mock_run_child.return_value = {"task_index": 0, "status": "completed", "summary": "ok", "api_calls": 1, "duration_seconds": 0.1}

        with patch("tools.delegate_tool._infer_delegate_tier", side_effect=AssertionError("heuristic should not run")):
            result = json.loads(delegate_task(goal="review this patch", tier="planning", parent_agent=_make_mock_parent()))

        self.assertEqual(result["results"][0]["status"], "completed")
        kwargs = mock_build_child.call_args.kwargs
        self.assertEqual(kwargs["max_iterations"], 40)
        self.assertEqual(kwargs["override_reasoning_effort"], "high")

    @patch("tools.delegate_tool._run_single_child")
    @patch("tools.delegate_tool._build_child_agent")
    @patch("tools.delegate_tool._resolve_delegation_credentials")
    @patch("tools.delegate_tool._load_config")
    @patch("tools.delegate_tool._get_max_concurrent_children")
    def test_single_task_falls_back_to_default_tier_when_auto_inconclusive(
        self,
        mock_max_children,
        mock_load_config,
        mock_resolve_creds,
        mock_build_child,
        mock_run_child,
    ):
        mock_max_children.return_value = 3
        mock_load_config.return_value = {
            "model": "gpt-5.4-mini",
            "max_iterations": 25,
            "auto_tier_selection": True,
            "default_tier": "heavy",
            "tiers": {
                "heavy": {"reasoning_effort": "low", "max_iterations": 50},
            },
        }
        mock_resolve_creds.return_value = {
            "model": "gpt-5.4-mini",
            "provider": None,
            "base_url": None,
            "api_key": None,
            "api_mode": None,
        }
        mock_build_child.return_value = MagicMock()
        mock_run_child.return_value = {"task_index": 0, "status": "completed", "summary": "ok", "api_calls": 1, "duration_seconds": 0.1}

        with patch("tools.delegate_tool._infer_delegate_tier", return_value=None):
            result = json.loads(delegate_task(goal="implement", parent_agent=_make_mock_parent()))

        self.assertEqual(result["results"][0]["status"], "completed")
        kwargs = mock_build_child.call_args.kwargs
        self.assertEqual(kwargs["max_iterations"], 50)
        self.assertEqual(kwargs["override_reasoning_effort"], "medium")

    @patch("tools.delegate_tool._run_single_child")
    @patch("tools.delegate_tool._build_child_agent")
    @patch("tools.delegate_tool._resolve_delegation_credentials")
    @patch("tools.delegate_tool._load_config")
    @patch("tools.delegate_tool._get_max_concurrent_children")
    def test_batch_task_without_own_tier_inherits_top_level_tier(
        self,
        mock_max_children,
        mock_load_config,
        mock_resolve_creds,
        mock_build_child,
        mock_run_child,
    ):
        mock_max_children.return_value = 3
        mock_load_config.return_value = {
            "model": "gpt-5.4-mini",
            "max_iterations": 25,
            "tiers": {
                "heavy": {"reasoning_effort": "low", "max_iterations": 50},
                "light": {"reasoning_effort": "low", "max_iterations": 10},
            },
        }
        mock_resolve_creds.return_value = {
            "model": "gpt-5.4-mini",
            "provider": None,
            "base_url": None,
            "api_key": None,
            "api_mode": None,
        }
        mock_build_child.side_effect = [MagicMock(), MagicMock()]
        mock_run_child.side_effect = [
            {"task_index": 0, "status": "completed", "summary": "a", "api_calls": 1, "duration_seconds": 0.1},
            {"task_index": 1, "status": "completed", "summary": "b", "api_calls": 1, "duration_seconds": 0.1},
        ]

        result = json.loads(
            delegate_task(
                tier="heavy",
                tasks=[
                    {"goal": "implement feature"},
                    {"goal": "list files", "tier": "light"},
                ],
                parent_agent=_make_mock_parent(),
            )
        )

        self.assertEqual(len(result["results"]), 2)
        first_kwargs = mock_build_child.call_args_list[0].kwargs
        second_kwargs = mock_build_child.call_args_list[1].kwargs
        self.assertEqual(first_kwargs["max_iterations"], 50)
        self.assertEqual(first_kwargs["override_reasoning_effort"], "medium")
        self.assertEqual(second_kwargs["max_iterations"], 10)
        self.assertEqual(second_kwargs["override_reasoning_effort"], "low")


if __name__ == "__main__":
    unittest.main()
