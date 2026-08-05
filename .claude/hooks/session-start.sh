#!/usr/bin/env bash
# Sun Prototype Kit — Session Start Hook
# Injects pipeline awareness into every new session.
# Detects project state from .sun/ and provides context to Claude.

set -euo pipefail

# Detect project root (look for .sun/ or CLAUDE.md)
PROJECT_ROOT="$PWD"

# Build context message
CONTEXT=""

# Check if .sun/ exists (existing project)
if [ -d "$PROJECT_ROOT/.sun" ]; then
    # Read state if available
    if [ -f "$PROJECT_ROOT/.sun/STATE.md" ]; then
        PHASE=$(grep -i "phase:" "$PROJECT_ROOT/.sun/STATE.md" 2>/dev/null | head -1 | sed 's/.*phase:\s*//i' || echo "unknown")
        CONTEXT="Sun Prototype Kit project detected. Current phase: $PHASE. Read .sun/STATE.md for full context before taking action."
    else
        CONTEXT="Sun Prototype Kit project detected (.sun/ exists but no STATE.md). Check .sun/ directory for project state."
    fi
else
    CONTEXT="No .sun/ directory found. If starting a new project, use the takumi skill to begin the pipeline."
fi

# Add Iron Laws reminder
CONTEXT="$CONTEXT

IRON LAWS (non-negotiable):
1. NO PRODUCTION CODE WITHOUT A FAILING TEST FIRST
2. NO FIXES WITHOUT ROOT CAUSE INVESTIGATION FIRST
3. NO COMPLETION CLAIMS WITHOUT FRESH VERIFICATION EVIDENCE

Available skills: run \`/tkm:help\` to list current skills in the project."

# Output for Claude Code hook system
printf '%s' "{\"hookSpecificOutput\":{\"additionalContext\":$(printf '%s' "$CONTEXT" | python3 -c 'import json,sys; print(json.dumps(sys.stdin.read()))' 2>/dev/null || echo "\"$CONTEXT\"")}}"
