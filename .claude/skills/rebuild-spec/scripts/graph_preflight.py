#!/usr/bin/env python3
"""[GRAPHIFY-INTEGRATION] Deterministic graphify preflight for rebuild-spec.

Replaces prose preflight steps so the (re)index is CODE-enforced. The Knowledge Graph is
ON BY DEFAULT (config graphify.enabled). rebuild-spec runs this command every run; it
no-ops only when graphify is disabled. Behavior:
  - Enabled [default]: ensure `graphifyy` importable in the kit venv (lazy pip install),
    then `graphify update .` to (re)index cwd, and add graphify-out/ to .gitignore.
  - Disabled -> no-op => vanilla. Disabled when config `graphify.enabled` is false, or
    env REBUILD_NO_GRAPH=1 / GRAPHIFY_DISABLE=1 (hard opt-out).
Config is read from .claude/.tkm.json (local, wins) then ~/.claude/.tkm.json (global);
default True when the file/key is absent. Legacy --enable / REBUILD_USE_GRAPH still
force-enable (redundant now). Always exits 0; any failure degrades to "no graph".
"""
import json, os, subprocess, sys


def _run(py, args, cwd):
    try:
        return subprocess.run([py, *args], cwd=cwd, capture_output=True, text=True, timeout=600)
    except Exception:
        return None


def _config_graphify_enabled() -> bool:
    """Read graphify.enabled from config. Local .takumi.json (what the tkm CLI /
    `tkm graphify` writes) → local .tkm.json → global .takumi.json → global .tkm.json;
    first that defines it wins. Default True when absent; only an explicit `false`
    disables. (Reading .takumi.json is scoped to the KG toggle — no broader migration.)"""
    for p in (os.path.join(os.getcwd(), ".claude", ".takumi.json"),
              os.path.join(os.getcwd(), ".claude", ".tkm.json"),
              os.path.expanduser("~/.claude/.takumi.json"),
              os.path.expanduser("~/.claude/.tkm.json")):
        try:
            with open(p, encoding="utf-8") as f:
                cfg = json.load(f)
        except Exception:
            continue
        g = cfg.get("graphify") if isinstance(cfg, dict) else None
        if isinstance(g, dict) and "enabled" in g:
            return g["enabled"] is not False
    return True


def _enabled() -> bool:
    """ON by default. Hard off via env (REBUILD_NO_GRAPH / GRAPHIFY_DISABLE); otherwise
    follow config graphify.enabled (default True). Legacy force-on env kept for compat."""
    if os.environ.get("REBUILD_NO_GRAPH") == "1" or os.environ.get("GRAPHIFY_DISABLE") == "1":
        return False
    if os.environ.get("REBUILD_USE_GRAPH") == "1" or "--enable" in sys.argv[1:]:
        return True  # legacy force-on (redundant; default is already on)
    return _config_graphify_enabled()


def main() -> None:
    cwd = os.getcwd()
    if not _enabled():
        if os.environ.get("REBUILD_NO_GRAPH") == "1" or os.environ.get("GRAPHIFY_DISABLE") == "1":
            print("graphify: disabled (env opt-out) -> vanilla")
        else:
            print("graphify: disabled (graphify.enabled=false) -> vanilla")
        return

    skills = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    venv_py = os.path.join(skills, ".venv", "bin", "python3")
    py = venv_py if os.path.exists(venv_py) else sys.executable

    r = _run(py, ["-m", "graphify", "--version"], cwd)
    if r is None or r.returncode != 0:
        ins = _run(py, ["-m", "pip", "install", "graphifyy==0.8.49"], cwd)  # pinned to a tested version; bump deliberately
        if ins is None or ins.returncode != 0:
            print("graphify: unavailable and install failed -> vanilla")
            return

    idx = _run(py, ["-m", "graphify", "update", "."], cwd)
    graph = os.path.join(cwd, "graphify-out", "graph.json")
    if idx is None or idx.returncode != 0 or not os.path.exists(graph):
        print("graphify: index failed -> vanilla")
        return

    # Make a short `graphify` command available on PATH so the gated directives can use the
    # bare form. (Deliberately NOT running `graphify claude install`: the always-on
    # CLAUDE.md/PreToolUse-hook nudge writes into the user's project and showed no measured
    # token benefit — the structural saving comes from graph_to_scout, not runtime nudges.)
    venv_bin_graphify = os.path.join(os.path.dirname(py), "graphify")
    try:
        # Only link into an ALREADY-existing, ALREADY-on-PATH ~/.local/bin. Never create
        # the dir or otherwise mutate the user's PATH as a side effect (and skip if it
        # would be unused, e.g. macOS where ~/.local/bin is often not on PATH).
        local_bin = os.path.expanduser("~/.local/bin")
        on_path = local_bin in os.environ.get("PATH", "").split(os.pathsep)
        link = os.path.join(local_bin, "graphify")
        if on_path and os.path.isdir(local_bin) and os.path.exists(venv_bin_graphify) and not os.path.exists(link):
            os.symlink(venv_bin_graphify, link)
    except Exception:
        pass

    gi = os.path.join(cwd, ".gitignore")
    try:
        existing = open(gi, encoding="utf-8").read() if os.path.exists(gi) else ""
        if "graphify-out" not in existing:
            sep = "" if (existing == "" or existing.endswith("\n")) else "\n"
            with open(gi, "a", encoding="utf-8") as f:
                f.write(sep + "graphify-out/\n")
    except Exception:
        pass

    print("graphify: graph ready (graphify-out/graph.json)")


if __name__ == "__main__":
    main()
