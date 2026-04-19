#!/bin/bash
# Claude Code PreCompact hook — preserve Hermes memory through compaction.
#
# Install in Claude Code settings.json:
#   "hooks": {
#     "PreCompact": [{
#       "hooks": [{
#         "type": "command",
#         "command": "~/.hermes/mcp-servers/hooks/on-pre-compact.sh"
#       }]
#     }]
#   }
#
# Returns Hermes memory as additionalContext JSON so the compactor
# knows to preserve it in the summary. Without this, Hermes memory
# read earlier in the session is lost after compaction.

set -euo pipefail

HERMES_MEMORIES="${HERMES_HOME:-$HOME/.hermes}/memories"
MEMORY_FILE="$HERMES_MEMORIES/MEMORY.md"
USER_FILE="$HERMES_MEMORIES/USER.md"

context=""

if [ -f "$MEMORY_FILE" ] && [ -s "$MEMORY_FILE" ]; then
    context+="Hermes MEMORY.md:"$'\n'"$(cat "$MEMORY_FILE")"$'\n\n'
fi

if [ -f "$USER_FILE" ] && [ -s "$USER_FILE" ]; then
    context+="Hermes USER.md:"$'\n'"$(cat "$USER_FILE")"$'\n'
fi

if [ -n "$context" ]; then
    # Escape for JSON and wrap in hookSpecificOutput format
    escaped=$(echo "$context" | python3 -c 'import sys,json; print(json.dumps(sys.stdin.read()))')
    echo "{\"hookSpecificOutput\":{\"hookEventName\":\"PreCompact\",\"additionalContext\":$escaped}}"
fi
