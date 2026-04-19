#!/bin/bash
# Claude Code SessionEnd hook — log session boundary for Hermes awareness.
#
# Install in Claude Code settings.json:
#   "hooks": {
#     "SessionEnd": [{
#       "hooks": [{
#         "type": "command",
#         "command": "~/.hermes/mcp-servers/hooks/on-session-end.sh"
#       }]
#     }]
#   }
#
# Writes a timestamped marker to a sync log so Hermes (or a cron job)
# can detect that a Claude Code session ended and may want to review
# any memory changes made during that session.
#
# NOTE: Claude Code SessionEnd hooks cannot call MCP tools (the server
# is already shutting down). This hook only writes a local marker file.

set -euo pipefail

HERMES_DIR="${HERMES_HOME:-$HOME/.hermes}"
SYNC_LOG="$HERMES_DIR/mcp-servers/hooks/sync.log"

mkdir -p "$(dirname "$SYNC_LOG")"

# Read session_id from stdin JSON if available
SESSION_ID=""
if read -t 1 input 2>/dev/null; then
    SESSION_ID=$(echo "$input" | python3 -c 'import sys,json; d=json.load(sys.stdin); print(d.get("session_id",""))' 2>/dev/null || true)
fi

echo "$(date -u +%Y-%m-%dT%H:%M:%SZ) session_end claude-code ${SESSION_ID}" >> "$SYNC_LOG"
