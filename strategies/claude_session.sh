#!/usr/bin/env bash
# Only a captured explicit UUID is safe across parallel same-directory panes.
CURRENT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
exec python3 "$CURRENT_DIR/../scripts/claude_sessions.py" restore "$1"
