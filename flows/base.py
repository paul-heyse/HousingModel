"""Base flow templates for ETL operations with common functionality."""

from __future__ import annotations

import functools
import time
from typing import Any, Callable, Dict, Optional, TypeVar

from prefect import flow, task
from prefect.context import get_run_context as prefect_get_run_context
from prefect.logging import get_logger

from aker_core.cache import fetch, get_cache
from aker_core.config import get_settings
from aker_core.logging import get_logger as get_structlog_logger
from aker_core.run import RunContext
from aker_data.lake import DataLake

F = TypeVar("F", bound=Callable[..., Any])

# Initialize core components (with error handling for missing env vars)
try:
    _settings = get_settings()
    _cache = get_cache()
    _lake = DataLake()
    _logger = get_logger(__name__)
    _structlog_logger = get_structlog_logger(__name__)
except Exception:
    # Fallback for testing/development without full environment setup
    _settings = None
    _cache = None
    _lake = None
    _logger = None
    _structlog_logger = None


def with_run_context(func: F) -> F:
    """Decorator to provide RunContext for database operations."""
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        # Only set up run context if components are available
        if not all([_cache, _lake]):
            return func(*args, **kwargs)

        # Get or create a RunContext for this execution
        try:
            # Try to get existing context from Prefect context
            context = prefect_get_run_context()
            run_ctx = getattr(context, "run_context", None)
        except Exception:
            run_ctx = None

        if run_ctx is None:
            def session_factory():
                from sqlalchemy import create_engine
                from sqlalchemy.orm import sessionmaker

                dsn = None
                if _settings is not None:
                    try:
                        dsn = _settings.postgis_dsn.get_secret_value()
                    except Exception:
                        dsn = None
                engine = create_engine(dsn or "sqlite:///flows.db")
                Session = sessionmaker(bind=engine)
                return Session()

            run_ctx = RunContext(session_factory)

        # Set the run context in the cache and lake
        if run_ctx:
            _cache.run_context = run_ctx
            _lake._run_context = run_ctx

        try:
            return func(*args, **kwargs)
        finally:
            # Clean up the run context
            if run_ctx:
                _cache.run_context = None
                _lake._run_context = None

    return wrapper


def etl_task(name: str, description: str = ""):
    """Decorator for ETL tasks with enhanced logging and error handling."""
    def decorator(func: F) -> F:
        @task(name=name, description=description, retries=2, retry_delay_seconds=30)
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            start_time = time.time()

            # Use fallback logger if Prefect logger not available
            try:
                task_logger = get_logger(f"{__name__}.{name}")
            except Exception:
                import logging
                task_logger = logging.getLogger(f"{__name__}.{name}")

            try:
                task_logger.info(f"Starting task: {name}")
                result = func(*args, **kwargs)
                duration = time.time() - start_time

                task_logger.info(
                    f"Completed task: {name}",
                    duration_seconds=duration,
                    success=True
                )

                # Log to structured logger if available
                if _structlog_logger:
                    _structlog_logger.info(
                        f"etl_task_completed",
                        task=name,
                        duration_ms=int(duration * 1000),
                        success=True
                    )

                return result

            except Exception as e:
                duration = time.time() - start_time
                task_logger.error(
                    f"Failed task: {name}",
                    error=str(e),
                    duration_seconds=duration
                )

                # Log to structured logger if available
                if _structlog_logger:
                    _structlog_logger.error(
                        f"etl_task_failed",
                        task=name,
                        error=str(e),
                        duration_ms=int(duration * 1000),
                        success=False
                    )
                raise

        return wrapper
    return decorator


def timed_flow(func: F) -> F:
    """Decorator to add timing and logging to flows."""
    @flow
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        flow_name = func.__name__
        start_time = time.time()

        # Use fallback logger if Prefect logger not available
        try:
            if _logger:
                _logger.info(f"Starting flow: {flow_name}")
        except Exception:
            import logging
            logging.info(f"Starting flow: {flow_name}")

        try:
            result = func(*args, **kwargs)
            duration = time.time() - start_time

            try:
                if _logger:
                    _logger.info(
                        f"Completed flow: {flow_name}",
                        duration_seconds=duration,
                        success=True
                    )
            except Exception:
                import logging
                logging.info(f"Completed flow: {flow_name} in {duration:.2f}s")

            # Log to structured logger if available
            if _structlog_logger:
                _structlog_logger.info(
                    f"flow_completed",
                    flow=flow_name,
                    duration_ms=int(duration * 1000),
                    success=True
                )

            return result

        except Exception as e:
            duration = time.time() - start_time

            try:
                if _logger:
                    _logger.error(
                        f"Failed flow: {flow_name}",
                        error=str(e),
                        duration_seconds=duration
                    )
            except Exception:
                import logging
                logging.error(f"Failed flow: {flow_name} after {duration:.2f}s: {e}")

            # Log to structured logger if available
            if _structlog_logger:
                _structlog_logger.error(
                    f"flow_failed",
                    flow=flow_name,
                    error=str(e),
                    duration_ms=int(duration * 1000),
                    success=False
                )
            raise

    return wrapper


def get_current_run_context() -> Optional[RunContext]:
    """Get the current Prefect RunContext if available."""

    try:
        context = prefect_get_run_context()
        return getattr(context, "run_context", None)
    except Exception:
        return None



# Backwards compatibility alias for existing imports
get_run_context = get_current_run_context


def log_etl_event(event: str, **kwargs):
    """Log an ETL event with structured data."""
    if _structlog_logger:
        _structlog_logger.info(
            f"etl_{event}",
            event=event,
            **kwargs
        )
    else:
        # Fallback to standard logging
        import logging
        logger = logging.getLogger(__name__)
        logger.info(f"ETL event: {event}", extra=kwargs)


class ETLFlow:
    """Base class for ETL flows with common functionality."""

    def __init__(self, name: str, description: str = ""):
        self.name = name
        self.description = description

        # Use fallback logger if Prefect logger not available
        try:
            self.logger = get_logger(f"flows.{name}")
        except Exception:
            import logging
            self.logger = logging.getLogger(f"flows.{name}")

    def log_start(self, **context):
        """Log flow start."""
        self.logger.info(f"Starting ETL flow: {self.name}", **context)
        log_etl_event("flow_start", flow=self.name, **context)

    def log_complete(self, duration: float, **context):
        """Log flow completion."""
        self.logger.info(
            f"Completed ETL flow: {self.name}",
            duration_seconds=duration,
            **context
        )
        log_etl_event(
            "flow_complete",
            flow=self.name,
            duration_ms=int(duration * 1000),
            **context
        )

    def log_error(self, error: str, duration: float, **context):
        """Log flow error."""
        self.logger.error(
            f"Failed ETL flow: {self.name}",
            error=error,
            duration_seconds=duration,
            **context
        )
        log_etl_event(
            "flow_error",
            flow=self.name,
            error=error,
            duration_ms=int(duration * 1000),
            **context
        )
