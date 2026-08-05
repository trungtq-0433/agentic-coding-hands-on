#!/usr/bin/env bash
# Install Python dependencies for the estimate skill.
# Requires Python 3.10+ (uses union type syntax: str | None).
#
# Usage: bash install-deps.sh [--venv /path/to/venv]
#
# Without --venv: installs into the shared skills venv at
#   ~/.claude/skills/.venv  (created via takumi-kit install scripts)

set -euo pipefail

SKILL_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REQ_FILE="$SKILL_DIR/requirements.txt"

VENV_PYTHON=""

# Parse args
while [[ $# -gt 0 ]]; do
    case "$1" in
        --venv)
            VENV_PYTHON="$2/bin/python3"
            shift 2
            ;;
        *)
            echo "Usage: $0 [--venv /path/to/venv]" >&2
            exit 1
            ;;
    esac
done

# Resolve interpreter: explicit venv > shared skills venv > system python 3.10+
if [[ -z "$VENV_PYTHON" ]]; then
    SHARED_VENV="$HOME/.claude/skills/.venv/bin/python3"
    if [[ -x "$SHARED_VENV" ]]; then
        VENV_PYTHON="$SHARED_VENV"
    fi
fi

if [[ -z "$VENV_PYTHON" ]]; then
    # Fall back to any python3 >= 3.10 on PATH
    for cmd in python3.14 python3.13 python3.12 python3.11 python3.10 \
               /opt/homebrew/bin/python3 /usr/local/bin/python3; do
        if command -v "$cmd" &>/dev/null; then
            if "$cmd" -c "import sys; sys.exit(0 if sys.version_info >= (3,10) else 1)" 2>/dev/null; then
                VENV_PYTHON="$cmd"
                break
            fi
        fi
    done
fi

if [[ -z "$VENV_PYTHON" ]]; then
    echo "ERROR: Python 3.10+ not found. Install via: brew install python@3.12" >&2
    exit 1
fi

echo "Using: $VENV_PYTHON ($($VENV_PYTHON --version))"
"$VENV_PYTHON" -m pip install -r "$REQ_FILE" --quiet

echo "Done. Verify with:"
echo "  $VENV_PYTHON -c \"import yaml, jsonschema, openpyxl, pandas; print('OK')\""
