"""Pytest fixtures shared across the migrate-aidd test suite."""
import sys
from pathlib import Path

# Ensure the scripts directory is on sys.path so test modules can import
# speckit_parse_lib and other helpers directly.
_SCRIPTS_DIR = Path(__file__).resolve().parent.parent
if str(_SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS_DIR))

FIXTURES_DIR = Path(__file__).resolve().parent / "fixtures"
REPO_ROOT = Path(__file__).resolve().parents[5]  # agent-kit/
SCRIPTS_DIR = _SCRIPTS_DIR
