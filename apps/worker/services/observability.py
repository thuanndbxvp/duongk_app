"""
Observability — structured JSON logging + Prometheus metrics.
Phase 07: All workers emit JSON events; expose metrics.
"""
from __future__ import annotations
import json
import time
from datetime import datetime, timezone
from dataclasses import dataclass, field, asdict
from typing import Literal

EventKind = Literal[
    "project_stage_started", "project_stage_completed", "project_stage_failed",
    "provider_call_started", "provider_call_completed", "provider_call_failed",
    "asset_materialized",
    "tts_duration_measured",
    "render_progress", "render_cancelled",
    "export_verified",
]


@dataclass
class LogEvent:
    """Structured JSON log event."""
    kind: EventKind
    timestamp: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    project_id: str = ""
    stage: str = ""
    provider: str = ""
    asset_id: str = ""
    duration_ms: float = 0
    error: str = ""
    metadata: dict = field(default_factory=dict)

    def emit(self):
        """Emit JSON log to stdout."""
        record = asdict(self)
        record['kind'] = self.kind
        print(json.dumps(record, default=str), flush=True)


# In-memory metrics (production: use prometheus_client)
_metrics: dict[str, float | int] = {
    "provider_success_total": 0,
    "provider_fail_total": 0,
    "tts_queue_wait_seconds": 0,
    "render_failure_total": 0,
    "render_cancelled_total": 0,
    "asset_orphan_count": 0,
    "cost_per_video_cents": 0,
}

# Latency histogram store
_stage_latencies: dict[str, list[float]] = {}


def record_stage_latency(stage: str, latency_ms: float):
    """Record stage latency for histogram."""
    if stage not in _stage_latencies:
        _stage_latencies[stage] = []
    _stage_latencies[stage].append(latency_ms)


def inc_counter(name: str, delta: int = 1):
    if name in _metrics:
        _metrics[name] += delta


def set_gauge(name: str, value: float | int):
    if name in _metrics:
        _metrics[name] = value


def get_metrics() -> dict:
    """Return current metrics snapshot."""
    result = dict(_metrics)
    for stage, lats in _stage_latencies.items():
        if lats:
            result[f"stage_latency_{stage}_avg_ms"] = sum(lats) / len(lats)
            result[f"stage_latency_{stage}_count"] = len(lats)
    return result


def reset_metrics():
    """Reset all metrics (for testing)."""
    for k in _metrics:
        _metrics[k] = 0
    _stage_latencies.clear()
