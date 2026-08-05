"""Self-contained dependency bootstrap for ephemeral sandboxes (e.g. Claude Desktop).

Why this exists
---------------
On a local/Takumi install the skill runs via `.claude/skills/.venv/bin/python3`
with deps pre-installed, and this module is a no-op (deps already importable).

On the Claude Desktop sandbox there is NO venv: the skill dir is mounted
**read-only**, the system `python3` often lacks the `pip` module, and bash calls
do not reliably share state. Earlier versions tried to `pip install -t scripts/.pkgs`
using a hardcoded `/usr/bin/python3` — that fails (read-only target + no pip) and
sends the agent into a retry spiral that ends in "Stream closed".

This module fixes all of that in ONE python process (immune to bash isolation):
  - installs into a **writable** dir, never the skill dir
  - uses `sys.executable` (the interpreter actually running), not a hardcoded path
  - bootstraps pip via `ensurepip`, and when that is ALSO stripped (the Desktop
    sandbox ships python with neither pip nor ensurepip), downloads get-pip.py
    into the writable dir and installs pip there — all in-process
  - forces prebuilt wheels (`--only-binary`) so lxml/Pillow never compile -> no timeout
  - idempotent guard: if deps already importable, do nothing
"""
from __future__ import annotations

import importlib
import importlib.util
import os
import subprocess
import sys
import tempfile
import urllib.request
from pathlib import Path

_SCRIPT_DIR = Path(__file__).resolve().parent
_REQUIREMENTS = _SCRIPT_DIR / "requirements.txt"
_GET_PIP_URL = "https://bootstrap.pypa.io/get-pip.py"


def _writable_pkg_dir() -> Path:
    """First writable candidate. NEVER under the (read-only) skill dir."""
    candidates = [
        os.environ.get("CLIO_PKG_DIR"),
        Path(tempfile.gettempdir()) / "clio_pkgs",
        Path.home() / ".cache" / "clio-generate" / "pkgs",
    ]
    for cand in candidates:
        if not cand:
            continue
        path = Path(cand)
        try:
            path.mkdir(parents=True, exist_ok=True)
            return path
        except OSError:
            continue
    # Last resort: a fresh temp dir is always writable.
    return Path(tempfile.mkdtemp(prefix="clio_pkgs_"))


def _read_requirements() -> list[str]:
    if not _REQUIREMENTS.exists():
        return ["python-pptx", "Pillow", "lxml", "requests"]
    reqs = []
    for line in _REQUIREMENTS.read_text(encoding="utf-8").splitlines():
        line = line.split("#", 1)[0].strip()
        if line:
            reqs.append(line)
    return reqs


def _pip_env(pkg_dir: Path) -> dict:
    """Return an environment in which `python -m pip` works.

    Tries, in order: existing pip -> ensurepip -> get-pip.py download. The last
    one is required on the Desktop sandbox, whose python has neither pip nor
    ensurepip. pip is installed into a writable subdir and exposed via PYTHONPATH.
    """
    env = os.environ.copy()
    if importlib.util.find_spec("pip") is not None:
        return env

    # ensurepip if available
    if importlib.util.find_spec("ensurepip") is not None:
        subprocess.run([sys.executable, "-m", "ensurepip", "--user"], check=False)
        importlib.invalidate_caches()
        if importlib.util.find_spec("pip") is not None:
            return env

    # last resort: get-pip.py into a writable dir, exposed via PYTHONPATH
    pip_home = pkg_dir / "_pip"
    pip_home.mkdir(parents=True, exist_ok=True)
    get_pip = pkg_dir / "get-pip.py"
    with urllib.request.urlopen(_GET_PIP_URL, timeout=60) as resp:
        get_pip.write_bytes(resp.read())
    subprocess.check_call([
        sys.executable, str(get_pip),
        "--target", str(pip_home),
        "--no-warn-script-location", "-q",
    ])
    env["PYTHONPATH"] = os.pathsep.join(
        p for p in (str(pip_home), env.get("PYTHONPATH", "")) if p
    )
    return env


def ensure_deps(probe: str = "pptx") -> None:
    """Make skill deps importable. No-op when already present.

    `probe` is the lightest module that signals the full set is installed.
    """
    pkg_dir = _writable_pkg_dir()
    # Put the writable target first so a prior install is found before re-installing.
    if str(pkg_dir) not in sys.path:
        sys.path.insert(0, str(pkg_dir))

    if importlib.util.find_spec(probe) is not None:
        return  # already importable (venv install or previous bootstrap)

    env = _pip_env(pkg_dir)  # guarantees `python -m pip` is usable
    subprocess.check_call(
        [
            sys.executable, "-m", "pip", "install",
            "--only-binary=:all:",   # prebuilt wheels only -> no native compile, no timeout
            "--no-input", "-q",
            "-t", str(pkg_dir),      # writable target, NOT the read-only skill dir
            *_read_requirements(),
        ],
        env=env,
    )
    importlib.invalidate_caches()

    if importlib.util.find_spec(probe) is None:
        raise RuntimeError(
            f"Dependency bootstrap finished but '{probe}' still not importable "
            f"(install target: {pkg_dir})."
        )
