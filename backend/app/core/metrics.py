"""Lightweight Prometheus-compatible metrics for the API.

Designed to be dependency-free (no `prometheus_client` library required) so the
project remains small and free-tier friendly. Output is Prometheus text format,
which any standard scraper (Prometheus, VictoriaMetrics, Grafana Cloud Agent,
…) can ingest.
"""

import threading
import time
from collections import defaultdict

# Record process start time at module load for process_uptime_seconds
_process_start_time = time.time()


class Counter:
    """A monotonically increasing counter keyed by an arbitrary tuple of labels."""

    def __init__(self, name: str, help_text: str) -> None:
        self.name = name
        self.help = help_text
        self._values: dict[tuple[tuple[str, str], ...], float] = defaultdict(float)
        self._lock = threading.Lock()

    def inc(self, amount: float = 1.0, **labels: str) -> None:
        key = tuple(sorted(labels.items()))
        with self._lock:
            self._values[key] += amount

    def render(self) -> list[str]:
        with self._lock:
            return [self._format(key, value) for key, value in self._values.items()]

    def _format(self, key: tuple[tuple[str, str], ...], value: float) -> str:
        if not key:
            return f"{self.name} {value}"
        label_str = ",".join(f'{k}="{v}"' for k, v in key)
        return f"{self.name}{{{label_str}}} {value}"


class Histogram:
    """Approximate histogram (count + sum + fixed buckets) keyed by labels."""

    DEFAULT_BUCKETS = (0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0)

    def __init__(self, name: str, help_text: str, buckets: tuple[float, ...] = DEFAULT_BUCKETS) -> None:
        self.name = name
        self.help = help_text
        self.buckets = buckets
        self._lock = threading.Lock()
        # buckets[key][bucket_index] = count
        self._bucket_counts: dict[tuple[tuple[str, str], ...], list[int]] = defaultdict(
            lambda: [0] * len(self.buckets)
        )
        self._sums: dict[tuple[tuple[str, str], ...], float] = defaultdict(float)
        self._counts: dict[tuple[tuple[str, str], ...], int] = defaultdict(int)

    def observe(self, value: float, **labels: str) -> None:
        key = tuple(sorted(labels.items()))
        with self._lock:
            bucket_counts = self._bucket_counts[key]
            for i, upper in enumerate(self.buckets):
                if value <= upper:
                    bucket_counts[i] += 1
                    break
            self._sums[key] += value
            self._counts[key] += 1

    def render(self) -> list[str]:
        with self._lock:
            lines: list[str] = []
            for key in self._bucket_counts:
                label_prefix = ",".join(f'{k}="{v}"' for k, v in key)
                cumulative = 0
                for i, upper in enumerate(self.buckets):
                    # Add current bucket count to running total (Prometheus
                    # histograms are cumulative: bucket(0.01) >= bucket(0.005))
                    cumulative += self._bucket_counts[key][i]
                    le = f',le="{upper}"'
                    label = label_prefix + le if label_prefix else f'le="{upper}"'
                    lines.append(f"{self.name}_bucket{{{label}}} {cumulative}")
                # +Inf bucket (all observations fall into this)
                label = label_prefix + ',le="+Inf"' if label_prefix else 'le="+Inf"'
                lines.append(f"{self.name}_bucket{{{label}}} {self._counts[key]}")
                lines.append(f"{self.name}_count{{{label_prefix}}} {self._counts[key]}")
                lines.append(f"{self.name}_sum{{{label_prefix}}} {self._sums[key]}")
            return lines


# ---------------------------------------------------------------------------
# Built-in application metrics
# ---------------------------------------------------------------------------

http_requests_total = Counter(
    "http_requests_total",
    "Total number of HTTP requests received",
)
http_request_duration_seconds = Histogram(
    "http_request_duration_seconds",
    "HTTP request latency in seconds",
)
http_requests_in_flight = Counter(
    "http_requests_in_flight",
    "Number of HTTP requests currently in flight",
)
http_request_errors_total = Counter(
    "http_request_errors_total",
    "Total number of HTTP requests that resulted in an error (status >= 400)",
)


def render_prometheus_metrics() -> str:
    """Render all metrics in Prometheus text format."""
    process_uptime = time.time() - _process_start_time
    lines = [
        "# HELP process_uptime_seconds Process uptime in seconds",
        "# TYPE process_uptime_seconds gauge",
        f"process_uptime_seconds {process_uptime:.2f}",
    ]
    for c in [http_requests_total, http_request_errors_total]:
        lines += [f"# HELP {c.name} {c.help}", f"# TYPE {c.name} counter"]
        lines += c.render()
    for h in [http_request_duration_seconds]:
        lines += [f"# HELP {h.name} {h.help}", f"# TYPE {h.name} histogram"]
        lines += h.render()
    return "\n".join(lines) + "\n"
