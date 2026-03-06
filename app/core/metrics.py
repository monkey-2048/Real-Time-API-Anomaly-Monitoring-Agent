from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass
from datetime import datetime, timezone
from threading import Lock


@dataclass
class MetricPoint:
    count: int = 0
    total_ms: float = 0.0


class MetricsRegistry:
    def __init__(self) -> None:
        self._counters: defaultdict[str, int] = defaultdict(int)
        self._latencies: defaultdict[str, MetricPoint] = defaultdict(MetricPoint)
        self._gauges: dict[str, float] = {}
        self._events: dict[str, str] = {}
        self._lock = Lock()

    def incr(self, key: str, value: int = 1) -> None:
        with self._lock:
            self._counters[key] += value

    def observe_ms(self, key: str, latency_ms: float) -> None:
        with self._lock:
            point = self._latencies[key]
            point.count += 1
            point.total_ms += latency_ms

    def set_gauge(self, key: str, value: float) -> None:
        with self._lock:
            self._gauges[key] = value

    def mark_event(self, key: str) -> None:
        with self._lock:
            self._events[key] = datetime.now(timezone.utc).isoformat()

    def snapshot(self) -> dict:
        with self._lock:
            latency_summary = {
                key: {
                    "count": point.count,
                    "avg_ms": (point.total_ms / point.count if point.count else 0.0),
                }
                for key, point in self._latencies.items()
            }
            return {
                "counters": dict(self._counters),
                "latencies": latency_summary,
                "gauges": dict(self._gauges),
                "events": dict(self._events),
            }


metrics = MetricsRegistry()
