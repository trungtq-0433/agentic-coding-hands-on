"""NestJS microservices topology adapter (Phase D, RT2-F8).

Signal → field mapping (documented per contract):
  @EventPattern('order.placed')   → topic[]{name="order.placed", role="consumer", event=""}
  @MessagePattern('cmd.place')    → topic[]{name="cmd.place",    role="consumer", event=""}
  emit/send via ClientProxy.send  → topic[]{name=<t>,            role="producer", event=""}
  @GrpcMethod('SvcName','Method') → rpc[]{name="Method",         direction="inbound",  message=""}
  client.send('cmd', payload)     → topic[]{name="cmd",           role="producer", event=""}

Stdlib only. All signals extracted via regex line-scan (no AST).
"""
from __future__ import annotations

import re
from pathlib import Path
from typing import Any

# ---------------------------------------------------------------------------
# Compiled patterns
# ---------------------------------------------------------------------------

# @EventPattern('order.placed') or @EventPattern("order.placed")
_EVENT_PATTERN = re.compile(r"@EventPattern\s*\(\s*['\"]([^'\"]+)['\"]")

# @MessagePattern('cmd') or @MessagePattern("cmd")
_MSG_PATTERN   = re.compile(r"@MessagePattern\s*\(\s*['\"]([^'\"]+)['\"]")

# ClientProxy.send('cmd', ...) — outbound producer. Review H2: require a client/proxy-named
# receiver so generic .send()/.emit() (HttpService, mailer, EventEmitter, Redis) don't inflate
# the graph with phantom producer edges. Also gated on a @nestjs/microservices import (below).
_CLIENT_SEND   = re.compile(r"\b(?:this\.)?\w*(?:client|proxy)\w*\s*\.\s*send\s*\(\s*['\"]([^'\"]+)['\"]", re.IGNORECASE)

# ClientProxy.emit('event', ...) — outbound fire-and-forget producer (same receiver guard)
_CLIENT_EMIT   = re.compile(r"\b(?:this\.)?\w*(?:client|proxy)\w*\s*\.\s*emit\s*\(\s*['\"]([^'\"]+)['\"]", re.IGNORECASE)

# Gate: only trust .send/.emit as message producers when the microservices client is in play.
_MICROSERVICES_IMPORT = re.compile(r"@nestjs/microservices|ClientProxy|ClientKafka|ClientProxyFactory")

# @GrpcMethod('ServiceName', 'MethodName')
_GRPC_METHOD   = re.compile(r"@GrpcMethod\s*\([^)]*['\"](\w+)['\"]")


def _scan_ts_file(path: Path) -> tuple[list[dict], list[dict]]:
    """Return (topics, rpcs) extracted from a single TypeScript source file."""
    try:
        text = path.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return [], []

    topics: list[dict[str, Any]] = []
    rpcs:   list[dict[str, Any]] = []

    for m in _EVENT_PATTERN.finditer(text):
        topics.append({"name": m.group(1), "role": "consumer", "event": ""})

    for m in _MSG_PATTERN.finditer(text):
        topics.append({"name": m.group(1), "role": "consumer", "event": ""})

    # Producer edges only when the microservices client is imported in this file (review H2).
    if _MICROSERVICES_IMPORT.search(text):
        for m in _CLIENT_SEND.finditer(text):
            topics.append({"name": m.group(1), "role": "producer", "event": ""})
        for m in _CLIENT_EMIT.finditer(text):
            topics.append({"name": m.group(1), "role": "producer", "event": ""})

    for m in _GRPC_METHOD.finditer(text):
        rpcs.append({"name": m.group(1), "direction": "inbound", "message": ""})

    return topics, rpcs


# ---------------------------------------------------------------------------
# Public adapter entry-point
# ---------------------------------------------------------------------------

def extract(component_root: str) -> dict[str, Any]:
    """Walk component_root for NestJS microservice signals; return neutral-digest fragments.

    Returns {"topic": [...], "rpc": [...]}.
    Duplicates de-duplicated by (name, role) / (name, direction).
    """
    root = Path(component_root)
    all_topics: list[dict[str, Any]] = []
    all_rpcs:   list[dict[str, Any]] = []

    _SKIP = {"node_modules", "dist", ".git", "coverage", "__pycache__", ".venv"}

    for dirpath, dirnames, filenames in _os_walk(root):
        dirnames[:] = [d for d in dirnames if d not in _SKIP]
        for fn in filenames:
            if fn.endswith((".ts", ".js")):
                fp = Path(dirpath) / fn
                t, r = _scan_ts_file(fp)
                all_topics.extend(t)
                all_rpcs.extend(r)

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
    """Portable os.walk wrapper."""
    import os
    for dp, dn, fn in os.walk(str(root), followlinks=False):
        yield Path(dp), dn, fn
