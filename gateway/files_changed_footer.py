"""Helpers for optional final-response files-changed footer in gateway mode."""

from __future__ import annotations

import json
import os
from typing import Any

_ENABLE_VALUES = {"1", "true", "yes", "on"}


def is_files_changed_footer_enabled() -> bool:
    """Return True when final-response files footer is enabled via env var."""
    raw = str(os.getenv("HERMES_FINAL_RESPONSE_FILES_CHANGED_FOOTER", "") or "").strip().lower()
    return raw in _ENABLE_VALUES


def _safe_parse_json_obj(raw_payload: Any) -> dict[str, Any] | None:
    if not isinstance(raw_payload, str):
        return None
    payload = raw_payload.strip()
    if not payload or not payload.startswith("{"):
        return None
    try:
        parsed = json.loads(payload)
    except Exception:
        return None
    return parsed if isinstance(parsed, dict) else None


def _normalize_changed_path(raw_path: Any) -> str:
    if raw_path is None:
        return ""
    path = str(raw_path).strip()
    if not path:
        return ""
    if " -> " in path:
        left, right = path.split(" -> ", 1)
        path = right.strip() or left.strip()
    if path.startswith("a/") or path.startswith("b/"):
        path = path[2:]
    return path


def _count_unified_diff(diff_text: str) -> dict[str, dict[str, int]]:
    stats: dict[str, dict[str, int]] = {}
    current_path = ""
    for raw_line in str(diff_text or "").splitlines():
        line = raw_line.rstrip("\n")
        if line.startswith("diff --git "):
            parts = line.split()
            if len(parts) >= 4:
                candidate = parts[3]
                if candidate.startswith("b/"):
                    candidate = candidate[2:]
                current_path = _normalize_changed_path(candidate)
                if current_path:
                    stats.setdefault(current_path, {"add": 0, "del": 0})
            continue
        if line.startswith("+++ "):
            candidate = line[4:].strip()
            if candidate == "/dev/null":
                current_path = ""
            else:
                current_path = _normalize_changed_path(candidate)
                if current_path:
                    stats.setdefault(current_path, {"add": 0, "del": 0})
            continue
        if line.startswith("@@"):
            continue
        if line.startswith("+") and not line.startswith("+++"):
            if current_path:
                stats.setdefault(current_path, {"add": 0, "del": 0})["add"] += 1
            continue
        if line.startswith("-") and not line.startswith("---"):
            if current_path:
                stats.setdefault(current_path, {"add": 0, "del": 0})["del"] += 1
            continue
    return stats


def build_files_changed_footer(agent_messages: list[dict[str, Any]], history_offset: int = 0) -> str:
    """Build a deterministic markdown footer from tool-call file edits."""
    if not agent_messages:
        return ""

    tool_call_meta: dict[str, dict[str, Any]] = {}
    for msg in agent_messages:
        if msg.get("role") != "assistant":
            continue
        for tool_call in (msg.get("tool_calls") or []):
            if not isinstance(tool_call, dict):
                continue
            call_id = str(tool_call.get("id") or "").strip()
            fn_data = tool_call.get("function") or {}
            fn_name = str(fn_data.get("name") or "").strip()
            fn_args = fn_data.get("arguments")
            parsed_args: dict[str, Any] = {}
            if isinstance(fn_args, str) and fn_args.strip():
                try:
                    candidate_args = json.loads(fn_args)
                    if isinstance(candidate_args, dict):
                        parsed_args = candidate_args
                except Exception:
                    parsed_args = {}
            elif isinstance(fn_args, dict):
                parsed_args = fn_args
            if call_id:
                tool_call_meta[call_id] = {
                    "name": fn_name,
                    "args": parsed_args,
                }

    start_idx = 0
    if isinstance(history_offset, int):
        start_idx = max(0, min(history_offset, len(agent_messages)))

    file_stats: dict[str, dict[str, int]] = {}
    for msg in agent_messages[start_idx:]:
        if msg.get("role") != "tool":
            continue
        payload = _safe_parse_json_obj(msg.get("content"))
        if not payload:
            continue

        call_id = str(msg.get("tool_call_id") or "").strip()
        meta = tool_call_meta.get(call_id, {})
        tool_name = str(meta.get("name") or "").strip()
        tool_args = meta.get("args") if isinstance(meta.get("args"), dict) else {}

        paths: list[str] = []
        for key in ("files_modified", "files_created", "files_deleted"):
            raw_paths = payload.get(key)
            if isinstance(raw_paths, list):
                for raw_path in raw_paths:
                    normalized = _normalize_changed_path(raw_path)
                    if normalized:
                        paths.append(normalized)

        if not paths and isinstance(tool_args, dict):
            arg_path = _normalize_changed_path(tool_args.get("path"))
            if arg_path and tool_name in ("write_file", "patch"):
                paths.append(arg_path)

        unique_paths: list[str] = []
        seen_paths = set()
        for path in paths:
            if path not in seen_paths:
                seen_paths.add(path)
                unique_paths.append(path)
        paths = unique_paths
        if not paths:
            continue

        diff_stats = _count_unified_diff(str(payload.get("diff") or ""))
        for path in paths:
            file_stats.setdefault(path, {"add": 0, "del": 0})

        if diff_stats:
            matched_any = False
            for path in paths:
                if path in diff_stats:
                    file_stats[path]["add"] += int(diff_stats[path].get("add", 0))
                    file_stats[path]["del"] += int(diff_stats[path].get("del", 0))
                    matched_any = True
            if not matched_any:
                total_add = sum(int(v.get("add", 0)) for v in diff_stats.values())
                total_del = sum(int(v.get("del", 0)) for v in diff_stats.values())
                file_stats[paths[0]]["add"] += total_add
                file_stats[paths[0]]["del"] += total_del
        elif tool_name == "write_file" and isinstance(tool_args, dict):
            content_arg = tool_args.get("content")
            if isinstance(content_arg, str) and content_arg:
                line_count = content_arg.count("\n")
                if not content_arg.endswith("\n"):
                    line_count += 1
                file_stats[paths[0]]["add"] += max(1, line_count)

    nonzero_stats = {
        path: stats
        for path, stats in file_stats.items()
        if int(stats.get("add", 0) or 0) or int(stats.get("del", 0) or 0)
    }
    if not nonzero_stats:
        return ""

    ordered_paths = sorted(nonzero_stats.keys())
    total_add = sum(int(v.get("add", 0) or 0) for v in nonzero_stats.values())
    total_del = sum(int(v.get("del", 0) or 0) for v in nonzero_stats.values())
    lines = [f"## 📁 {len(ordered_paths)} Files Changed +{total_add} -{total_del}"]
    for path in ordered_paths:
        add = int(nonzero_stats[path].get("add", 0) or 0)
        dele = int(nonzero_stats[path].get("del", 0) or 0)
        deltas = []
        if add:
            deltas.append(f"+{add}")
        if dele:
            deltas.append(f"-{dele}")
        if not deltas:
            continue
        lines.append(f"- {path} {' '.join(deltas)}")
    return "\n".join(lines)
