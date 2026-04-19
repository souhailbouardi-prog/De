import json

import pytest

from gateway.files_changed_footer import (
    build_files_changed_footer,
    is_files_changed_footer_enabled,
)


def _assistant_tool_call(call_id: str, name: str, args: dict) -> dict:
    return {
        "role": "assistant",
        "tool_calls": [
            {
                "id": call_id,
                "function": {
                    "name": name,
                    "arguments": json.dumps(args),
                },
            }
        ],
    }


def _tool_result(call_id: str, payload: dict) -> dict:
    return {
        "role": "tool",
        "tool_call_id": call_id,
        "content": json.dumps(payload),
    }


def test_footer_toggle_defaults_to_disabled(monkeypatch):
    monkeypatch.delenv("HERMES_FINAL_RESPONSE_FILES_CHANGED_FOOTER", raising=False)
    assert is_files_changed_footer_enabled() is False


@pytest.mark.parametrize("value", ["1", "true", "TRUE", "yes", "on"])
def test_footer_toggle_enabled_truthy_values(monkeypatch, value):
    monkeypatch.setenv("HERMES_FINAL_RESPONSE_FILES_CHANGED_FOOTER", value)
    assert is_files_changed_footer_enabled() is True


def test_build_footer_returns_empty_for_invalid_or_empty_payloads():
    messages = [
        {"role": "assistant", "tool_calls": []},
        {"role": "tool", "tool_call_id": "a", "content": "not-json"},
        {"role": "tool", "tool_call_id": "b", "content": "{}"},
    ]
    assert build_files_changed_footer(messages) == ""


def test_build_footer_is_deterministic_and_english_header():
    messages = [
        _assistant_tool_call("call_1", "patch", {"path": "src/z.py"}),
        _assistant_tool_call("call_2", "patch", {"path": "src/a.py"}),
        _tool_result(
            "call_1",
            {
                "files_modified": ["src/z.py"],
                "diff": "\n".join(
                    [
                        "diff --git a/src/z.py b/src/z.py",
                        "--- a/src/z.py",
                        "+++ b/src/z.py",
                        "@@ -1 +1,2 @@",
                        "-old",
                        "+new",
                        "+line2",
                    ]
                ),
            },
        ),
        _tool_result(
            "call_2",
            {
                "files_modified": ["src/a.py"],
                "diff": "\n".join(
                    [
                        "diff --git a/src/a.py b/src/a.py",
                        "--- a/src/a.py",
                        "+++ b/src/a.py",
                        "@@ -1,2 +1 @@",
                        "-old1",
                        "-old2",
                        "+new1",
                    ]
                ),
            },
        ),
    ]

    footer = build_files_changed_footer(messages)
    lines = footer.splitlines()

    assert lines[0] == "## 📁 2 Files Changed +3 -3"
    assert lines[1] == "- src/a.py +1 -2"
    assert lines[2] == "- src/z.py +2 -1"


def test_build_footer_uses_write_file_path_fallback_and_line_count():
    messages = [
        _assistant_tool_call(
            "call_1",
            "write_file",
            {"path": "notes/todo.md", "content": "a\nb\n"},
        ),
        _tool_result("call_1", {"ok": True}),
    ]

    footer = build_files_changed_footer(messages)
    assert footer == "\n".join(
        [
            "## 📁 1 Files Changed +2 -0",
            "- notes/todo.md +2",
        ]
    )
