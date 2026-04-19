#!/bin/bash
# Claude Code SessionStart hook — inject Hermes memory into context.
#
# Install in Claude Code settings.json:
#   "hooks": {
#     "SessionStart": [{
#       "matcher": "startup|resume|compact",
#       "hooks": [{
#         "type": "command",
#         "command": "~/.hermes/mcp-servers/hooks/on-session-start.sh"
#       }]
#     }]
#   }
#
# On startup/resume/compact, reads Hermes MEMORY.md and USER.md and
# writes them to stdout so Claude Code injects them as context.
# This ensures Hermes memory survives context compaction.

set -euo pipefail

HERMES_MEMORIES="${HERMES_HOME:-$HOME/.hermes}/memories"
MEMORY_FILE="$HERMES_MEMORIES/MEMORY.md"
USER_FILE="$HERMES_MEMORIES/USER.md"

output=""

if [ -f "$MEMORY_FILE" ] && [ -s "$MEMORY_FILE" ]; then
    output+="[Hermes Memory]"$'\n'
    output+="$(cat "$MEMORY_FILE")"$'\n\n'
fi

if [ -f "$USER_FILE" ] && [ -s "$USER_FILE" ]; then
    output+="[Hermes User Profile]"$'\n'
    output+="$(cat "$USER_FILE")"$'\n'
fi

if [ -n "$output" ]; then
    echo "$output"
fi
