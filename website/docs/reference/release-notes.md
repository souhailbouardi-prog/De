---
title: Release Notes
---

# Release Notes

## 2026-04-19 — Quiet single-query output hardening

Hermes CLI single-query mode (`hermes chat -q ...`) got a programmatic output cleanup focused on automation wrappers and shell integrations.

What changed:

- Fixed duplicate final answers in `--quiet` mode when non-interactive streaming callbacks were still attached.
- Tightened quiet text output so it prints:
  1. the final response
  2. `session_id: <id>` on the next line
  3. no blank spacer line between them
- Added `--format json` for quiet single-query mode.
- Added `--include-metadata` for quiet JSON output when wrappers want a small structured metadata block.
- Standardized failure output so Hermes emits `Error: ...` even when the underlying run failed without a populated `final_response`.

Examples:

```bash
# Stable text output
hermes chat -q "2+2は？" --quiet

# Stable JSON output
hermes chat -q "2+2は？" --quiet --format json

# Stable JSON output with metadata
hermes chat -q "2+2は？" --quiet --format json --include-metadata
```

JSON contract:

```json
{"ok": true, "response": "4", "session_id": "20260419_135733_e10f98"}
```

JSON + metadata contract:

```json
{"ok": true, "response": "4", "session_id": "20260419_135733_e10f98", "metadata": {"format": "json", "failed": false, "model": "gpt-5.4", "provider": "openai-codex"}}
```

Failure contract:

```json
{"ok": false, "response": "Error: rate limited", "session_id": "...", "error": "rate limited"}
```

Constraints:

- `--format json` is supported only for quiet single-query mode.
- `--include-metadata` requires `--format json`.
- Using `--format json` without `--quiet` returns a CLI error instead of mixing human and machine-oriented output.

Verification:

- CLI help updated to show `--format {text,json}` and `--include-metadata`
- Quiet text/json tests added and passing
- Real command smoke tests run for both text and JSON output
