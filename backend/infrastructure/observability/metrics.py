from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class Counter:
    name: str
    labels: dict[str, str] = field(default_factory=dict)
    _value: float = 0.0

    def inc(self, amount: float = 1.0) -> None:
        self._value += amount


@dataclass
class Histogram:
    name: str
    labels: dict[str, str] = field(default_factory=dict)
    _observations: list[float] = field(default_factory=list)

    def observe(self, value: float) -> None:
        self._observations.append(value)


class MetricsRegistry:
    """
    Lightweight in-process metrics registry.

    Production: replace with prometheus_client or OpenTelemetry metrics SDK.
    """

    def __init__(self):
        self._counters: dict[str, Counter] = {}
        self._histograms: dict[str, Histogram] = {}

    def counter(self, name: str, labels: dict[str, str] | None = None) -> Counter:
        key = self._key(name, labels)
        if key not in self._counters:
            self._counters[key] = Counter(name=name, labels=labels or {})
        return self._counters[key]

    def histogram(self, name: str, labels: dict[str, str] | None = None) -> Histogram:
        key = self._key(name, labels)
        if key not in self._histograms:
            self._histograms[key] = Histogram(name=name, labels=labels or {})
        return self._histograms[key]

    def _key(self, name: str, labels: dict[str, str] | None) -> str:
        if not labels:
            return name
        label_str = ",".join(f"{k}={v}" for k, v in sorted(labels.items()))
        return f"{name}{{{label_str}}}"

    def export_prometheus(self) -> str:
        lines: list[str] = []
        for counter in self._counters.values():
            label_str = self._format_labels(counter.labels)
            lines.append(f"{counter.name}{label_str} {counter._value}")
        for hist in self._histograms.values():
            if hist._observations:
                label_str = self._format_labels(hist.labels)
                lines.append(f"{hist.name}_count{label_str} {len(hist._observations)}")
                lines.append(f"{hist.name}_sum{label_str} {sum(hist._observations)}")
        return "\n".join(lines) + "\n"

    @staticmethod
    def _format_labels(labels: dict[str, str]) -> str:
        if not labels:
            return ""
        inner = ",".join(f'{k}="{v}"' for k, v in sorted(labels.items()))
        return f"{{{inner}}}"


metrics = MetricsRegistry()