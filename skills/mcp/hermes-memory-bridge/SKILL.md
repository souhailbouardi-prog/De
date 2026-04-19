---
name: hermes-memory-bridge
description: Expose Hermes MEMORY.md, USER.md, and session history (state.db) to external MCP clients (Claude Code, Cursor, VS Code, etc.) via a FastMCP stdio server. Includes Claude Code lifecycle hooks for memory injection, compaction survival, and session-end tracking.
version: 1.0.0
author: easyvibecoding
license: MIT
metadata:
  hermes:
    tags: [MCP, Memory, Claude Code, Integration, Bridge, Hooks]
    related_skills: [native-mcp, claude-code]
---

# Hermes Memory Bridge

Expose Hermes Agent's persistent memory system (MEMORY.md, USER.md) and session history (state.db) to any MCP-compatible client via a lightweight FastMCP stdio server, with Claude Code lifecycle hooks for memory synchronization.

## Problem

`hermes mcp serve` exposes conversation browsing tools but does **not** expose memory read/write or session transcript access. External agents like Claude Code cannot access Hermes memory without a custom bridge. Even with MCP access, the two systems have independent lifecycles — Hermes uses frozen snapshots and `on_session_end` hooks, while Claude Code uses `SessionStart`/`PreCompact`/`SessionEnd` hooks — and neither side is aware of the other's memory changes.

## How This Relates to Existing Memory Consolidation

Hermes already has **in-process** memory lifecycle hooks:

| Hook | Trigger | Used by |
|------|---------|---------|
| `on_session_end(messages)` | CLI exit, `/reset`, gateway timeout | Honcho: flush to cloud; Holographic: regex fact extraction |
| `on_memory_write(action, target, content)` | Built-in `memory` tool writes | Holographic: mirror to fact store |
| `on_pre_compress(messages)` | Before context compression | All providers: inject into summary |
| `sync_turn(user, asst)` | After each turn | Honcho/Mem0: background sync |
| `prefetch(query)` / `queue_prefetch` | Before/after API call | Background recall for next turn |

These run **inside** the Hermes process. This bridge provides **out-of-process** access for external MCP clients.

**Key limitation**: When an external MCP client writes to MEMORY.md directly, Hermes's `on_memory_write` hook does **not** fire (it only triggers for writes through the built-in `memory` tool). Holographic's fact-store mirror and similar provider integrations will not see MCP-originated writes.

## Lifecycle Integration

### The Problem: Two Independent Lifecycles

```
Hermes lifecycle:              Claude Code lifecycle:
┌─────────────────────┐       ┌─────────────────────────┐
│ Session start       │       │ SessionStart hook        │
│  └─ load_from_disk()│       │  └─ loads CLAUDE.md,     │
│     (frozen snapshot)│       │     auto-memory          │
│                     │       │     ❌ no Hermes memory   │
│ Per-turn:           │       │ Per-turn:                │
│  ├─ prefetch()      │       │  ├─ MCP tool calls       │
│  ├─ sync_turn()     │       │  └─ Stop hook            │
│  └─ on_memory_write │       │                          │
│     (internal only) │       │ /compact:                │
│                     │       │  ├─ PreCompact hook      │
│ Session end:        │       │  │  ❌ Hermes memory lost │
│  ├─ on_session_end()│       │  └─ PostCompact          │
│  └─ shutdown()      │       │                          │
│                     │       │ SessionEnd hook           │
│                     │       │  ❌ no sync back          │
└─────────────────────┘       └─────────────────────────┘
```

### The Solution: Hook Scripts

Three Claude Code hook scripts bridge the lifecycle gaps:

**`on-session-start.sh`** — Injects Hermes memory into Claude Code context at session start, resume, and after compaction.

```
SessionStart (startup|resume|compact)
  → reads MEMORY.md + USER.md from disk
  → writes to stdout → Claude Code injects as context
```

**`on-pre-compact.sh`** — Preserves Hermes memory through context compaction by returning it as `additionalContext` JSON.

```
PreCompact
  → reads MEMORY.md + USER.md
  → returns {"additionalContext": "..."} JSON
  → compactor includes it in the summary
```

**`on-session-end.sh`** — Logs a session boundary marker so Hermes (or a cron job) can detect when a Claude Code session ended.

```
SessionEnd
  → writes timestamp + session_id to sync.log
  → Hermes cron or next session can check for changes
```

**Note**: `SessionEnd` hooks cannot call MCP tools (the server is shutting down), so only local file operations are possible at this stage.

## Installation

### 1. Copy files

```bash
cp mcp-servers/hermes-memory-mcp.py ~/.hermes/mcp-servers/
cp mcp-servers/hermes-memory-runner.sh ~/.hermes/mcp-servers/
cp -r mcp-servers/hooks/ ~/.hermes/mcp-servers/hooks/
chmod +x ~/.hermes/mcp-servers/hermes-memory-runner.sh
chmod +x ~/.hermes/mcp-servers/hooks/*.sh
```

### 2. Register MCP server

**Hermes** (`~/.hermes/config.yaml`):

```yaml
mcp_servers:
  hermes-memory:
    command: ~/.hermes/mcp-servers/hermes-memory-runner.sh
    args: []
    enabled: true
```

**Claude Code** (`~/.claude.json` or `.claude/settings.local.json`):

```json
{
  "mcpServers": {
    "hermes-memory": {
      "command": "/bin/bash",
      "args": ["~/.hermes/mcp-servers/hermes-memory-runner.sh"]
    }
  }
}
```

### 3. Register hooks (Claude Code)

Add to `~/.claude/settings.json`:

```json
{
  "hooks": {
    "SessionStart": [{
      "matcher": "startup|resume|compact",
      "hooks": [{
        "type": "command",
        "command": "~/.hermes/mcp-servers/hooks/on-session-start.sh",
        "timeout": 5000
      }]
    }],
    "PreCompact": [{
      "hooks": [{
        "type": "command",
        "command": "~/.hermes/mcp-servers/hooks/on-pre-compact.sh",
        "timeout": 5000
      }]
    }],
    "SessionEnd": [{
      "hooks": [{
        "type": "command",
        "command": "~/.hermes/mcp-servers/hooks/on-session-end.sh",
        "timeout": 3000
      }]
    }]
  }
}
```

### 4. Verify

```
> memory_status()
MEMORY.md: 892/2,200 chars (40.5%) — 5 sections
USER.md: 461/1,375 chars (33.5%) — 5 sections
state.db: 127 sessions (searchable via session_search)
```

## Tools (7)

### Memory

| Tool | Description |
|------|-------------|
| `read_memory(store)` | Read MEMORY.md, USER.md, or both |
| `add_memory_entry(store, entry, old_text)` | Append or substring-replace in a memory store |
| `remove_memory_entry(store, old_text)` | Remove a section or substring cleanly |
| `memory_status()` | Char usage, section count, state.db session count |

### Session

| Tool | Description |
|------|-------------|
| `recent_sessions(limit, source)` | List recent sessions |
| `session_read(session_id, last_n)` | Read full transcript of a session |
| `session_search(query, limit, source)` | FTS5 full-text search across all sessions |

## Safety

Aligned with Hermes built-in `tools/memory_tool.py`:

- **Atomic writes** — temp file + `os.replace()` + `fsync` prevents corruption on crash
- **Cross-platform file locking** — `fcntl.flock` (Unix) / `msvcrt.locking` (Windows) / graceful fallback
- **Prompt-injection scanning** — rejects role hijacking, instruction override, chat-template tokens, invisible Unicode
- **Read-only state.db** — all session queries use `?mode=ro`

## Architecture

```
~/.hermes/
├── memories/
│   ├── MEMORY.md              # General memory (2,200 char limit)
│   └── USER.md                # User profile (1,375 char limit)
├── state.db                   # SQLite with FTS5 session index
└── mcp-servers/
    ├── hermes-memory-mcp.py   # FastMCP server (7 tools)
    ├── hermes-memory-runner.sh# Shell wrapper for uv
    └── hooks/
        ├── on-session-start.sh    # SessionStart: inject Hermes memory
        ├── on-pre-compact.sh      # PreCompact: preserve through compaction
        └── on-session-end.sh      # SessionEnd: log boundary marker
```

### Known Limitations

1. **Frozen snapshot** — Hermes loads memory once at session start. MCP writes persist to disk but are invisible to the current Hermes session until it restarts.
2. **`on_memory_write` bypass** — MCP writes go directly to the file, bypassing Hermes's internal `memory` tool. Provider hooks like Holographic's fact-mirror will not trigger.
3. **SessionEnd cannot call MCP** — The MCP server shuts down before `SessionEnd` hooks run. Only local file operations are possible at session end.
4. **Two memory systems** — Claude Code has its own auto-memory (`~/.claude/projects/*/memory/`). This bridge does not merge the two; they coexist as separate stores.
