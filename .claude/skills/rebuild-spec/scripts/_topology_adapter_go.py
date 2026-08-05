"""Go microservices topology adapter (Phase D, RT2-F8).

Signal → field mapping (documented per contract):
  segmentio/kafka-go  kafka.NewReader(cfg) where cfg.Topic="t" → topic consumer
  segmentio/kafka-go  w.WriteMessages / kafka.NewWriter(cfg)   → topic producer
  sarama              consumer.ConsumePartition("t", ...)      → topic consumer
  sarama              producer.SendMessage(&sarama.ProducerMsg{Topic:"t"}) → topic producer
  gRPC stub (.pb.go)  func (s *Server) MethodName(           → rpc inbound
  gRPC client stub    client.MethodName(ctx, req)             → rpc outbound (heuristic)

Stdlib only. All signals extracted via regex line-scan (no AST).
"""
from __future__ import annotations

import re
from pathlib import Path
from typing import Any

# ---------------------------------------------------------------------------
# Compiled patterns
# ---------------------------------------------------------------------------

# kafka-go NewReader / NewWriter config literal: Topic: "order.placed"
_KGO_TOPIC       = re.compile(r'Topic\s*:\s*"([^"]+)"')

# kafka-go w.WriteMessages / explicit producer
_KGO_WRITE       = re.compile(r'\.WriteMessages\s*\(')

# sarama ConsumerGroup / ConsumePartition topic arg
_SARAMA_CONSUME  = re.compile(r'ConsumePartition\s*\(\s*"([^"]+)"')
_SARAMA_TOPICS   = re.compile(r'ConsumePartition\s*\([^,]+,\s*\d+')   # for context

# sarama ProducerMessage Topic field
_SARAMA_PRODUCE  = re.compile(r'ProducerMessage\s*\{[^}]*Topic\s*:\s*"([^"]+)"', re.DOTALL)

# gRPC server method signature in .pb.go: ) MethodName(ctx context.Context,
_GRPC_SERVER_FN  = re.compile(r'\)\s+([A-Z]\w+)\s*\(ctx\s+context\.Context')

# gRPC client call: client.PlaceOrder( or stub.PlaceOrder(
_GRPC_CLIENT_CALL = re.compile(r'\b(?:client|stub|c|grpcClient)\s*\.\s*([A-Z]\w+)\s*\(')

# kafka-go NewReader/NewWriter scope lines to distinguish consumer vs producer
_KGO_READER      = re.compile(r'kafka\.NewReader\s*\(')
_KGO_WRITER      = re.compile(r'kafka\.NewWriter\s*\(|kafka\.Writer\s*\{')


def _scan_go_file(path: Path) -> tuple[list[dict], list[dict]]:
    """Return (topics, rpcs) extracted from a single .go source file."""
    try:
        text = path.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return [], []

    topics: list[dict[str, Any]] = []
    rpcs:   list[dict[str, Any]] = []

    is_pb = path.name.endswith(".pb.go") or path.name.endswith("_grpc.pb.go")

    if is_pb:
        # gRPC server-side inbound RPCs from generated .pb.go
        for m in _GRPC_SERVER_FN.finditer(text):
            rpcs.append({"name": m.group(1), "direction": "inbound", "message": ""})
    else:
        # kafka-go: determine consumer vs producer by surrounding context
        # Simple heuristic: scan for NewReader/NewWriter blocks and pick up Topic
        lines = text.splitlines()
        mode: str | None = None
        for line in lines:
            if _KGO_READER.search(line):
                mode = "consumer"
            elif _KGO_WRITER.search(line) or _KGO_WRITE.search(line):
                mode = "producer"
            m = _KGO_TOPIC.search(line)
            if m and mode:
                topics.append({"name": m.group(1), "role": mode, "event": ""})

        # sarama consumer
        for m in _SARAMA_CONSUME.finditer(text):
            topics.append({"name": m.group(1), "role": "consumer", "event": ""})

        # sarama producer
        for m in _SARAMA_PRODUCE.finditer(text):
            topics.append({"name": m.group(1), "role": "producer", "event": ""})

        # gRPC outbound client calls (heuristic)
        for m in _GRPC_CLIENT_CALL.finditer(text):
            rpcs.append({"name": m.group(1), "direction": "outbound", "message": ""})

    return topics, rpcs


# ---------------------------------------------------------------------------
# Public adapter entry-point
# ---------------------------------------------------------------------------

def extract(component_root: str) -> dict[str, Any]:
    """Walk component_root for Go kafka/gRPC signals; return neutral-digest fragments.

    Returns {"topic": [...], "rpc": [...]}.
    Duplicates de-duplicated by (name, role) / (name, direction).
    """
    root = Path(component_root)
    all_topics: list[dict[str, Any]] = []
    all_rpcs:   list[dict[str, Any]] = []

    _SKIP = {"vendor", ".git", "dist", "node_modules", "__pycache__", ".venv"}

    for dirpath, dirnames, filenames in _os_walk(root):
        dirnames[:] = [d for d in dirnames if d not in _SKIP]
        for fn in filenames:
            if fn.endswith(".go"):
                fp = Path(dirpath) / fn
                t, r = _scan_go_file(fp)
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
