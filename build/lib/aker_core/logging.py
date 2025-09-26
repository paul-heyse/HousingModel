"""Structured logging and metrics helpers for the Aker platform."""

from __future__ import annotations

import json
import logging
import sys
import time
from contextlib import contextmanager
from dataclasses import dataclass
from enum import Enum
from typing import Any, Dict, Iterator, Optional, Tuple

import structlog
from structlog import contextvars as structlog_contextvars

try:  # pragma: no cover - optional dependency guard (should be available in prod)
    from prometheus_client import (
        CollectorRegistry,
        Counter,
        Histogram,
        generate_latest,
        make_wsgi_app,
        start_http_server,
    )
except Exception:  # pragma: no cover - fallback when metrics optional
    CollectorRegistry = None  # type: ignore
    Counter = Histogram = None  # type: ignore
    generate_latest = make_wsgi_app = start_http_server = None  # type: ignore


BoundLogger = structlog.stdlib.BoundLogger


@dataclass(frozen=True)
class ErrorClassification:
    """Represents a classified error with normalized metadata."""

    error_type: str
    error_code: str
    category: str
    severity: "ErrorSeverity"


class ErrorSeverity(str, Enum):
    """Severity levels used in the error taxonomy."""

    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


_CONFIGURED = False
_COUNTERS: Dict[Tuple[str, Tuple[str, ...]], Counter] = {}
_HISTOGRAMS: Dict[Tuple[str, Tuple[str, ...]], Histogram] = {}
_REGISTRY: Optional[CollectorRegistry] = CollectorRegistry() if CollectorRegistry else None


def configure_logging(
    *,
    level: int | str = logging.INFO,
    stream: Any | None = None,
    reconfigure: bool = False,
) -> None:
    """Configure structlog for JSON output."""

    global _CONFIGURED
    if _CONFIGURED and not reconfigure:
        return

    stream = stream or sys.stdout
    logging.basicConfig(level=level, stream=stream, format="%(message)s", force=True)

    structlog.configure(
        processors=[
            structlog_contextvars.merge_contextvars,
            structlog.processors.add_log_level,
            structlog.processors.TimeStamper(fmt="iso", key="timestamp"),
            structlog.processors.dict_tracebacks,
            structlog.processors.JSONRenderer(),
        ],
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=True,
    )

    _CONFIGURED = True


def reset_logging() -> None:
    """Reset logging configuration (primarily for tests)."""

    global _CONFIGURED
    _CONFIGURED = False
    _COUNTERS.clear()
    _HISTOGRAMS.clear()
    try:
        structlog_contextvars.clear_contextvars()
    except Exception:  # pragma: no cover - defensive
        pass
    if CollectorRegistry is not None:
        globals()["_REGISTRY"] = CollectorRegistry()


def _ensure_configured() -> None:
    if not _CONFIGURED:
        configure_logging()


def get_logger(name: str) -> BoundLogger:
    """Return a structured logger for the given module name."""

    _ensure_configured()
    return structlog.get_logger(name)


def _metric_key(name: str, labels: Dict[str, Any]) -> Tuple[str, Tuple[str, ...]]:
    return name, tuple(sorted(labels.keys()))


def increment_counter(
    name: str,
    description: str,
    *,
    amount: float = 1.0,
    **labels: Any,
) -> None:
    """Increment (or create) a named Prometheus counter."""

    if Counter is None or _REGISTRY is None:  # pragma: no cover - occurs if dependency optional
        return

    key = _metric_key(name, labels)
    counter = _COUNTERS.get(key)
    if counter is None:
        counter = Counter(name, description, list(sorted(labels.keys())), registry=_REGISTRY)
        _COUNTERS[key] = counter
    if labels:
        counter.labels(**labels).inc(amount)
    else:
        counter.inc(amount)


def observe_duration(
    name: str,
    description: str,
    value_seconds: float,
    **labels: Any,
) -> None:
    """Record a duration in seconds using a Prometheus histogram."""

    if Histogram is None or _REGISTRY is None:  # pragma: no cover - occurs if dependency optional
        return

    key = _metric_key(name, labels)
    histogram = _HISTOGRAMS.get(key)
    if histogram is None:
        histogram = Histogram(name, description, list(sorted(labels.keys())), registry=_REGISTRY)
        _HISTOGRAMS[key] = histogram
    if labels:
        histogram.labels(**labels).observe(value_seconds)
    else:
        histogram.observe(value_seconds)


def get_counter_metric(name: str, *, label_names: Tuple[str, ...] = ()) -> Counter | None:
    """Expose counters for testing/inspection."""

    return _COUNTERS.get((name, label_names))


def get_histogram_metric(name: str, *, label_names: Tuple[str, ...] = ()) -> Histogram | None:
    """Expose histograms for testing/inspection."""

    return _HISTOGRAMS.get((name, label_names))


def get_metrics_registry() -> Optional[CollectorRegistry]:
    """Return the CollectorRegistry used for Prometheus metrics."""

    return _REGISTRY


@contextmanager
def log_timing(
    logger: BoundLogger,
    event: str,
    *,
    metric_name: str | None = None,
    metric_description: str = "Duration in seconds",
    level: str = "info",
    extra: Optional[Dict[str, Any]] = None,
    labels: Optional[Dict[str, Any]] = None,
) -> Iterator[None]:
    """Context manager that logs timing/perf data for a block of code."""

    start = time.perf_counter()
    cpu_start = time.process_time()
    memory_start: Optional[Tuple[int, int]] = None
    tracemalloc_started = False
    try:  # pragma: no cover - tracemalloc optional
        import tracemalloc

        if not tracemalloc.is_tracing():
            tracemalloc.start()
            tracemalloc_started = True
        memory_start = tracemalloc.get_traced_memory()
    except Exception:
        memory_start = None
    error: Optional[BaseException] = None
    try:
        yield
    except BaseException as exc:  # pragma: no cover
        error = exc
        raise
    finally:
        duration_ms = (time.perf_counter() - start) * 1000.0
        cpu_ms = (time.process_time() - cpu_start) * 1000.0
        memory_delta_kb: Optional[float] = None
        try:  # pragma: no cover - tracemalloc optional
            import tracemalloc

            if memory_start is not None:
                current = tracemalloc.get_traced_memory()[0]
                memory_delta_kb = (current - memory_start[0]) / 1024.0
            if tracemalloc_started:
                tracemalloc.stop()
        except Exception:
            memory_delta_kb = None
        payload: Dict[str, Any] = dict(extra or {})
        payload["duration_ms"] = round(duration_ms, 3)
        payload["cpu_time_ms"] = round(cpu_ms, 3)
        if memory_delta_kb is not None:
            payload["memory_delta_kb"] = round(memory_delta_kb, 3)
        log_method = getattr(logger, level if error is None else "error", logger.info)
        log_method(event, **payload)
        if metric_name:
            observe_duration(
                metric_name,
                metric_description,
                duration_ms / 1000.0,
                **(labels or {}),
            )


def log_counter(
    logger: BoundLogger,
    event: str,
    name: str,
    description: str,
    *,
    amount: float = 1.0,
    level: str = "info",
    labels: Optional[Dict[str, Any]] = None,
    extra: Optional[Dict[str, Any]] = None,
) -> None:
    """Increment a counter and emit a structured log entry."""

    increment_counter(name, description, amount=amount, **(labels or {}))
    payload = dict(extra or {})
    payload.setdefault("count", amount)
    if labels:
        payload.update({f"label_{key}": value for key, value in labels.items()})
    getattr(logger, level, logger.info)(event, **payload)


def classify_error(error_type: str, severity: ErrorSeverity) -> ErrorClassification:
    """Create an error classification payload."""

    if ":" in error_type:
        category, code = error_type.split(":", 1)
    else:
        category, code = "general", error_type
    return ErrorClassification(
        error_type=error_type,
        error_code=code,
        category=category,
        severity=severity,
    )


def log_classified_error(
    logger: BoundLogger,
    event: str,
    classification: ErrorClassification,
    *,
    exc_info: Optional[BaseException] = None,
    **fields: Any,
) -> None:
    """Log an error with taxonomy metadata."""

    payload = dict(fields)
    payload["error_type"] = classification.error_type
    payload["error_code"] = classification.error_code
    payload["category"] = classification.category
    payload["severity"] = classification.severity.value
    if exc_info is not None:
        payload["exception"] = repr(exc_info)
        payload["message"] = str(exc_info)
        logger.error(event, exc_info=exc_info, **payload)
    else:
        logger.error(event, **payload)


def generate_metrics() -> bytes:
    """Generate Prometheus metrics in exposition format."""

    if generate_latest is None or _REGISTRY is None:  # pragma: no cover
        return b""
    return generate_latest(_REGISTRY)


def make_metrics_app():  # pragma: no cover - thin wrapper
    """Return a WSGI app exposing Prometheus metrics."""

    if make_wsgi_app is None or _REGISTRY is None:
        raise RuntimeError("Prometheus client is not available")
    return make_wsgi_app(_REGISTRY)


def start_metrics_server(
    port: int = 8000, addr: str = "0.0.0.0"
) -> None:  # pragma: no cover - network
    """Start an HTTP server that exposes Prometheus metrics."""

    if start_http_server is None or _REGISTRY is None:
        raise RuntimeError("Prometheus client is not available")
    start_http_server(port, addr, registry=_REGISTRY)


def parse_log_line(line: str) -> Dict[str, Any]:
    """Utility to parse a JSON log line (used in tests)."""

    return json.loads(line)


__all__ = [
    "BoundLogger",
    "configure_logging",
    "reset_logging",
    "get_logger",
    "log_timing",
    "log_counter",
    "increment_counter",
    "observe_duration",
    "classify_error",
    "log_classified_error",
    "ErrorSeverity",
    "ErrorClassification",
    "get_counter_metric",
    "get_histogram_metric",
    "get_metrics_registry",
    "generate_metrics",
    "make_metrics_app",
    "start_metrics_server",
    "parse_log_line",
]
