from __future__ import annotations

import io
import json

import pytest

import aker_core.logging as aker_logging


@pytest.fixture(autouse=True)
def reset_logging_state():
    aker_logging.reset_logging()
    yield
    aker_logging.reset_logging()


def _configure(stream: io.StringIO) -> None:
    aker_logging.configure_logging(stream=stream, reconfigure=True)


def test_get_logger_emits_structured_json():
    stream = io.StringIO()
    _configure(stream)
    logger = aker_logging.get_logger(__name__)

    logger.info("scored_market", msa="DEN", ms=42)

    record = json.loads(stream.getvalue().strip())
    assert record["event"] == "scored_market"
    assert record["msa"] == "DEN"
    assert record["ms"] == 42
    assert record["level"] == "info"
    assert "timestamp" in record


def test_log_timing_records_duration_and_metric():
    stream = io.StringIO()
    _configure(stream)
    logger = aker_logging.get_logger("metrics")

    with aker_logging.log_timing(
        logger,
        "heavy_step",
        metric_name="heavy_step_seconds",
        metric_description="Heavy step duration",
        labels={"stage": "load"},
    ):
        pass

    output = json.loads(stream.getvalue().strip())
    assert output["event"] == "heavy_step"
    assert "duration_ms" in output
    assert output["duration_ms"] >= 0
    assert "cpu_time_ms" in output

    histogram = aker_logging.get_histogram_metric("heavy_step_seconds", label_names=("stage",))
    assert histogram is not None
    metric_family = histogram.collect()[0]
    count_value = next(
        sample.value
        for sample in metric_family.samples
        if sample.name.endswith("_count") and sample.labels.get("stage") == "load"
    )
    assert count_value == 1
    if "memory_delta_kb" in output:
        assert isinstance(output["memory_delta_kb"], (int, float))


def test_log_timing_error_path_logs_error():
    stream = io.StringIO()
    _configure(stream)
    logger = aker_logging.get_logger("error_metrics")

    with pytest.raises(RuntimeError):
        with aker_logging.log_timing(
            logger,
            "failing_step",
            metric_name="failing_step_seconds",
        ):
            raise RuntimeError("boom")

    record = json.loads(stream.getvalue().strip())
    assert record["event"] == "failing_step"
    assert record["level"] == "error"
    assert record["duration_ms"] >= 0


def test_log_counter_increments_counter_and_logs():
    stream = io.StringIO()
    _configure(stream)
    logger = aker_logging.get_logger("counter")

    aker_logging.log_counter(
        logger,
        "increment",
        name="pipeline_runs_total",
        description="Number of pipeline runs",
    )

    record = json.loads(stream.getvalue().strip())
    assert record["event"] == "increment"
    assert record["count"] == 1

    counter = aker_logging.get_counter_metric("pipeline_runs_total")
    assert counter is not None
    assert counter._value.get() == 1  # type: ignore[attr-defined]


def test_log_counter_with_labels_creates_labeled_metric():
    stream = io.StringIO()
    _configure(stream)
    logger = aker_logging.get_logger("counter")

    aker_logging.log_counter(
        logger,
        "increment_with_labels",
        name="pipeline_runs_total",
        description="Number of pipeline runs",
        labels={"environment": "test"},
    )

    record = json.loads(stream.getvalue().strip())
    assert record["event"] == "increment_with_labels"
    assert record["label_environment"] == "test"

    counter = aker_logging.get_counter_metric("pipeline_runs_total", label_names=("environment",))
    assert counter is not None
    assert counter.labels(environment="test")._value.get() == 1  # type: ignore[attr-defined]


def test_log_classified_error_includes_taxonomy():
    stream = io.StringIO()
    _configure(stream)
    logger = aker_logging.get_logger("errors")

    classification = aker_logging.classify_error(
        "market_data_missing", aker_logging.ErrorSeverity.ERROR
    )

    aker_logging.log_classified_error(
        logger,
        "market_failure",
        classification,
        asset="example",
    )

    entry = json.loads(stream.getvalue().strip())
    assert entry["event"] == "market_failure"
    assert entry["error_type"] == "market_data_missing"
    assert entry["error_code"] == "market_data_missing"
    assert entry["category"] == "general"
    assert entry["severity"] == aker_logging.ErrorSeverity.ERROR.value
    assert entry["asset"] == "example"


def test_log_classified_error_with_exception_records_message():
    stream = io.StringIO()
    _configure(stream)
    logger = aker_logging.get_logger("errors")
    classification = aker_logging.classify_error(
        "pipeline_failure", aker_logging.ErrorSeverity.CRITICAL
    )

    try:
        raise ValueError("critical failure")
    except ValueError as exc:
        aker_logging.log_classified_error(
            logger,
            "pipeline_failure",
            classification,
            exc_info=exc,
            pipeline="market_scoring",
        )

    entry = json.loads(stream.getvalue().strip())
    assert entry["event"] == "pipeline_failure"
    assert entry["error_type"] == "pipeline_failure"
    assert entry["error_code"] == "pipeline_failure"
    assert entry["category"] == "general"
    assert entry["severity"] == aker_logging.ErrorSeverity.CRITICAL.value
    assert entry["pipeline"] == "market_scoring"
    assert entry["message"] == "critical failure"


def test_generate_metrics_returns_exposition():
    registry = aker_logging.get_metrics_registry()

    if registry is None:
        with pytest.raises(RuntimeError):
            aker_logging.generate_metrics()
    else:
        data = aker_logging.generate_metrics()
        assert isinstance(data, (bytes, bytearray))
        assert data.startswith(b"# HELP") or data.startswith(b"# TYPE")


def test_prometheus_helpers_invoke_registry(monkeypatch: pytest.MonkeyPatch) -> None:
    registry = aker_logging.get_metrics_registry()
    if registry is None:
        pytest.skip("Prometheus client not available")

    metrics_started = {}

    def fake_start_http_server(port, addr, registry=None):  # pragma: no cover - invoked in test
        metrics_started["port"] = port
        metrics_started["addr"] = addr
        metrics_started["registry"] = registry

    app_registry = {}

    def fake_make_wsgi_app(registry=None):  # pragma: no cover - invoked in test
        app_registry["registry"] = registry
        return lambda environ, start_response: None

    monkeypatch.setattr(aker_logging, "start_http_server", fake_start_http_server)
    monkeypatch.setattr(aker_logging, "make_wsgi_app", fake_make_wsgi_app)

    app = aker_logging.make_metrics_app()
    assert callable(app)
    assert app_registry["registry"] is registry

    aker_logging.start_metrics_server(port=9100, addr="127.0.0.1")
    assert metrics_started == {
        "port": 9100,
        "addr": "127.0.0.1",
        "registry": registry,
    }
