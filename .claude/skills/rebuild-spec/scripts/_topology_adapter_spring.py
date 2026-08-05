"""Spring Boot topology adapter (Phase D, RT2-F8).

Signal → field mapping (documented per contract):
  @KafkaListener(topics="<t>")  → topic[]{name=<t>, role="consumer", event=""}
  KafkaTemplate.send("<t>", …)  → topic[]{name=<t>, role="producer", event=""}
  @GrpcService / .proto rpc Foo → rpc[]{name="Foo", direction="inbound",  message="<req>"}
  stub.<method>(req)            → rpc[]{name="<method>", direction="outbound", message="<req>"}

Stdlib only. All signals extracted via regex line-scan (no AST).
"""
from __future__ import annotations

import re
from pathlib import Path
from typing import Any

# ---------------------------------------------------------------------------
# Compiled patterns
# ---------------------------------------------------------------------------

# @KafkaListener(topics = "order.placed") or topics={"a","b"}
_LISTENER_SINGLE = re.compile(r'@KafkaListener\s*\([^)]*topics\s*=\s*"([^"]+)"')
_LISTENER_MULTI  = re.compile(r'@KafkaListener\s*\([^)]*topics\s*=\s*\{([^}]+)\}')

# KafkaTemplate.send("order.placed", …)
_TEMPLATE_SEND   = re.compile(r'kafkaTemplate\.send\s*\(\s*"([^"]+)"')

# .proto: rpc MethodName (ReqMsg) returns (RespMsg)
_PROTO_RPC       = re.compile(r'^\s*rpc\s+(\w+)\s*\(\s*(\w+)\s*\)', re.MULTILINE)

# gRPC stub outbound: stub.placeOrder(req) — heuristic, Stub variable names
_GRPC_STUB_CALL  = re.compile(r'\bstub\s*\.\s*([a-z]\w+)\s*\((\w+)')


def _scan_java_file(path: Path) -> tuple[list[dict], list[dict]]:
    """Return (topics, rpcs) extracted from a single Java/Kotlin source file."""
    try:
        text = path.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return [], []

    topics: list[dict[str, Any]] = []
    rpcs:   list[dict[str, Any]] = []

    # Consumer topics — single
    for m in _LISTENER_SINGLE.finditer(text):
        topics.append({"name": m.group(1), "role": "consumer", "event": ""})

    # Consumer topics — multi
    for m in _LISTENER_MULTI.finditer(text):
        for raw in m.group(1).split(","):
            name = raw.strip().strip('"')
            if name:
                topics.append({"name": name, "role": "consumer", "event": ""})

    # Producer topics
    for m in _TEMPLATE_SEND.finditer(text):
        topics.append({"name": m.group(1), "role": "producer", "event": ""})

    # gRPC RPCs (review M1): inbound from .proto service defs, outbound from stub.<method>(req) calls.
    for m in _PROTO_RPC.finditer(text):
        rpcs.append({"name": m.group(1), "direction": "inbound", "message": m.group(2)})
    for m in _GRPC_STUB_CALL.finditer(text):
        rpcs.append({"name": m.group(1), "direction": "outbound", "message": m.group(2)})

    return topics, rpcs


def _scan_proto_file(path: Path) -> tuple[list[dict], list[dict]]:
    """Return (topics, rpcs) extracted from a .proto file."""
    try:
        text = path.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return [], []

    rpcs: list[dict[str, Any]] = []
    for m in _PROTO_RPC.finditer(text):
        rpcs.append({
            "name": m.group(1),
            "direction": "inbound",
            "message": m.group(2),
        })

    # Outbound stubs referenced in Java files nearby are caught in _scan_java_file.
    return [], rpcs


# ---------------------------------------------------------------------------
# Public adapter entry-point
# ---------------------------------------------------------------------------

def extract(component_root: str) -> dict[str, Any]:
    """Walk component_root for Spring signals; return neutral-digest fragments.

    Returns {"topic": [...], "rpc": [...]}.
    Unknown / uninspected items already filtered; duplicates de-duplicated by name+role.
    """
    root = Path(component_root)
    all_topics: list[dict[str, Any]] = []
    all_rpcs:   list[dict[str, Any]] = []

    _SKIP = {"node_modules", "vendor", "dist", "build", "__pycache__", ".git", ".venv", "target"}

    for dirpath, dirnames, filenames in root.walk() if hasattr(root, "walk") else _os_walk(root):
        dirnames[:] = [d for d in dirnames if d not in _SKIP]
        for fn in filenames:
            fp = Path(dirpath) / fn
            if fn.endswith((".java", ".kt")):
                t, r = _scan_java_file(fp)
                all_topics.extend(t)
                all_rpcs.extend(r)
            elif fn.endswith(".proto"):
                t, r = _scan_proto_file(fp)
                all_topics.extend(t)
                all_rpcs.extend(r)

    # De-duplicate by (name, role) / (name, direction)
    seen_t: set = set()
    topics = []
    for item in all_topics:
        key = (item["name"], item["role"])
        if key not in seen_t:
            seen_t.add(key)
            topics.append(item)

    seen_r: set = set()
    rpcs = []
    for item in all_rpcs:
        key = (item["name"], item["direction"])
        if key not in seen_r:
            seen_r.add(key)
            rpcs.append(item)

    return {"topic": topics, "rpc": rpcs}


def _os_walk(root: Path):
    """Fallback os.walk wrapper for Python < 3.12 (Path.walk added in 3.12)."""
    import os
    for dp, dn, fn in os.walk(str(root), followlinks=False):
        yield Path(dp), dn, fn
