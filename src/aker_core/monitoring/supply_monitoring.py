"""
Performance monitoring and profiling for supply constraint calculations.

Provides production monitoring, profiling, and alerting for supply calculators.
"""

from __future__ import annotations

import functools
import logging
import time
from collections import defaultdict, deque
from datetime import datetime, timedelta
from typing import Any, Callable, Dict, List, Optional, Union

import numpy as np

logger = logging.getLogger(__name__)


class SupplyPerformanceMonitor:
    """Performance monitoring for supply calculations."""

    def __init__(
        self,
        enable_profiling: bool = True,
        max_metrics_history: int = 1000,
        alert_thresholds: Optional[Dict[str, float]] = None
    ):
        """
        Initialize performance monitor.

        Args:
            enable_profiling: Whether to enable detailed profiling
            max_metrics_history: Maximum number of metric records to keep
            alert_thresholds: Custom alert thresholds
        """
        self.enable_profiling = enable_profiling
        self.max_metrics_history = max_metrics_history

        # Default alert thresholds
        self.alert_thresholds = alert_thresholds or {
            "calculation_time_ms": 5000,  # 5 seconds max
            "memory_usage_mb": 100,       # 100MB max
            "error_rate": 0.05,           # 5% error rate
            "data_quality_score": 0.8,    # 80% quality minimum
        }

        # Metrics storage
        self.metrics_history = deque(maxlen=max_metrics_history)
        self.error_counts = defaultdict(int)
        self.success_counts = defaultdict(int)

        # Performance counters
        self.total_calculations = 0
        self.total_errors = 0
        self.start_time = time.time()

    def profile_function(self, func_name: str):
        """
        Decorator to profile function performance.

        Args:
            func_name: Name of the function being profiled

        Returns:
            Decorated function
        """
        def decorator(func: Callable) -> Callable:
            @functools.wraps(func)
            def wrapper(*args, **kwargs):
                if not self.enable_profiling:
                    return func(*args, **kwargs)

                start_time = time.time()
                start_memory = self._get_memory_usage()

                try:
                    result = func(*args, **kwargs)

                    # Record successful execution
                    end_time = time.time()
                    end_memory = self._get_memory_usage()

                    execution_time = (end_time - start_time) * 1000  # Convert to ms
                    memory_delta = end_memory - start_memory

                    self._record_metric(func_name, {
                        "execution_time_ms": execution_time,
                        "memory_delta_mb": memory_delta,
                        "success": True,
                        "timestamp": datetime.now(),
                    })

                    self.success_counts[func_name] += 1

                    return result

                except Exception as e:
                    # Record failed execution
                    end_time = time.time()
                    execution_time = (end_time - start_time) * 1000

                    self._record_metric(func_name, {
                        "execution_time_ms": execution_time,
                        "success": False,
                        "error": str(e),
                        "timestamp": datetime.now(),
                    })

                    self.error_counts[func_name] += 1
                    self.total_errors += 1

                    raise

            return wrapper
        return decorator

    def _record_metric(self, func_name: str, metrics: Dict[str, Any]):
        """Record performance metrics."""
        metric_record = {
            "function": func_name,
            **metrics
        }

        self.metrics_history.append(metric_record)
        self.total_calculations += 1

    def _get_memory_usage(self) -> float:
        """Get current memory usage in MB."""
        try:
            import psutil
            process = psutil.Process()
            return process.memory_info().rss / (1024 * 1024)  # Convert to MB
        except ImportError:
            # Fallback for environments without psutil
            return 0.0

    def get_performance_summary(self, time_window_minutes: int = 60) -> Dict[str, Any]:
        """
        Get performance summary for the specified time window.

        Args:
            time_window_minutes: Time window in minutes for summary

        Returns:
            Performance summary statistics
        """
        cutoff_time = datetime.now() - timedelta(minutes=time_window_minutes)

        # Filter metrics by time window
        recent_metrics = [
            m for m in self.metrics_history
            if m["timestamp"] >= cutoff_time
        ]

        if not recent_metrics:
            return {
                "total_calculations": 0,
                "error_rate": 0.0,
                "avg_execution_time_ms": 0.0,
                "alerts": []
            }

        # Calculate summary statistics
        total_calculations = len(recent_metrics)
        successful_calculations = sum(1 for m in recent_metrics if m.get("success", False))
        error_rate = 1 - (successful_calculations / total_calculations) if total_calculations > 0 else 0

        execution_times = [m["execution_time_ms"] for m in recent_metrics if m.get("execution_time_ms")]
        avg_execution_time = np.mean(execution_times) if execution_times else 0

        # Check for alerts
        alerts = []

        if avg_execution_time > self.alert_thresholds["calculation_time_ms"]:
            threshold = self.alert_thresholds["calculation_time_ms"]
            alerts.append(
                {
                    "type": "performance",
                    "message": (
                        f"Average execution time {avg_execution_time:.1f}ms exceeds "
                        f"threshold {threshold}ms"
                    ),
                    "severity": "warning",
                }
            )

        if error_rate > self.alert_thresholds["error_rate"]:
            threshold = self.alert_thresholds["error_rate"]
            alerts.append(
                {
                    "type": "error_rate",
                    "message": (
                        f"Error rate {error_rate:.2%} exceeds threshold {threshold:.2%}"
                    ),
                    "severity": "error",
                }
            )

        return {
            "time_window_minutes": time_window_minutes,
            "total_calculations": total_calculations,
            "successful_calculations": successful_calculations,
            "error_rate": error_rate,
            "avg_execution_time_ms": avg_execution_time,
            "alerts": alerts,
            "uptime_seconds": time.time() - self.start_time
        }

    def get_function_breakdown(self) -> Dict[str, Dict[str, Any]]:
        """
        Get performance breakdown by function.

        Returns:
            Performance metrics by function name
        """
        function_metrics = defaultdict(list)

        for metric in self.metrics_history:
            func_name = metric["function"]
            function_metrics[func_name].append(metric)

        breakdown = {}

        for func_name, metrics in function_metrics.items():
            execution_times = [m["execution_time_ms"] for m in metrics if m.get("execution_time_ms")]
            success_count = sum(1 for m in metrics if m.get("success", False))
            total_count = len(metrics)

            breakdown[func_name] = {
                "total_calls": total_count,
                "successful_calls": success_count,
                "error_rate": 1 - (success_count / total_count) if total_count > 0 else 0,
                "avg_execution_time_ms": np.mean(execution_times) if execution_times else 0,
                "min_execution_time_ms": np.min(execution_times) if execution_times else 0,
                "max_execution_time_ms": np.max(execution_times) if execution_times else 0,
                "last_called": max(m["timestamp"] for m in metrics) if metrics else None
            }

        return dict(breakdown)

    def check_alerts(self) -> List[Dict[str, Any]]:
        """
        Check for performance alerts based on thresholds.

        Returns:
            List of current alerts
        """
        summary = self.get_performance_summary()

        alerts = []

        # Check calculation time
        if summary["avg_execution_time_ms"] > self.alert_thresholds["calculation_time_ms"]:
            alerts.append(
                {
                    "type": "performance_degradation",
                    "message": (
                        f"Average calculation time {summary['avg_execution_time_ms']:.1f}ms exceeds threshold"
                    ),
                    "severity": "warning",
                    "metric": "execution_time",
                    "current_value": summary["avg_execution_time_ms"],
                    "threshold": self.alert_thresholds["calculation_time_ms"],
                }
            )

        # Check error rate
        if summary["error_rate"] > self.alert_thresholds["error_rate"]:
            alerts.append(
                {
                    "type": "high_error_rate",
                    "message": (
                        f"Error rate {summary['error_rate']:.2%} exceeds threshold"
                    ),
                    "severity": "error",
                    "metric": "error_rate",
                    "current_value": summary["error_rate"],
                    "threshold": self.alert_thresholds["error_rate"],
                }
            )

        # Check if we have too few recent calculations
        if summary["total_calculations"] == 0:
            alerts.append({
                "type": "no_activity",
                "message": "No calculations recorded in monitoring period",
                "severity": "info",
                "metric": "activity",
                "current_value": 0,
                "threshold": 1
            })

        return alerts

    def export_metrics(self, format: str = "dict") -> Union[Dict[str, Any], str]:
        """
        Export performance metrics.

        Args:
            format: Export format ('dict', 'json', 'csv')

        Returns:
            Metrics in requested format
        """
        summary = self.get_performance_summary()
        breakdown = self.get_function_breakdown()
        alerts = self.check_alerts()

        metrics = {
            "summary": summary,
            "function_breakdown": breakdown,
            "alerts": alerts,
            "export_timestamp": datetime.now().isoformat(),
            "monitor_config": {
                "enable_profiling": self.enable_profiling,
                "max_metrics_history": self.max_metrics_history,
                "alert_thresholds": self.alert_thresholds
            }
        }

        if format == "json":
            import json
            return json.dumps(metrics, indent=2, default=str)
        elif format == "csv":
            # Convert to CSV format (basic implementation)
            lines = ["Metric,Value"]
            for key, value in summary.items():
                if isinstance(value, (int, float)):
                    lines.append(f"{key},{value}")
            return "\n".join(lines)
        else:
            return metrics

    def reset_metrics(self):
        """Reset all performance metrics and counters."""
        self.metrics_history.clear()
        self.error_counts.clear()
        self.success_counts.clear()
        self.total_calculations = 0
        self.total_errors = 0
        self.start_time = time.time()
        logger.info("Performance metrics reset")


# Global monitor instance
_supply_monitor = None

def get_supply_monitor() -> SupplyPerformanceMonitor:
    """Get the global supply performance monitor."""
    global _supply_monitor
    if _supply_monitor is None:
        _supply_monitor = SupplyPerformanceMonitor()
    return _supply_monitor

def profile_supply_function(func_name: str):
    """
    Convenience decorator for profiling supply functions.

    Args:
        func_name: Name of the function being profiled

    Returns:
        Decorator function
    """
    monitor = get_supply_monitor()
    return monitor.profile_function(func_name)


def log_supply_calculation(
    function_name: str,
    msa_id: str,
    execution_time_ms: float,
    success: bool,
    error: Optional[str] = None
):
    """
    Log a supply calculation for monitoring.

    Args:
        function_name: Name of the function
        msa_id: MSA identifier
        execution_time_ms: Execution time in milliseconds
        success: Whether the calculation succeeded
        error: Error message if calculation failed
    """
    monitor = get_supply_monitor()

    metrics = {
        "execution_time_ms": execution_time_ms,
        "success": success,
        "msa_id": msa_id,
        "timestamp": datetime.now(),
    }

    if error:
        metrics["error"] = error

    monitor._record_metric(function_name, metrics)

    if not success:
        monitor.error_counts[function_name] += 1
        monitor.total_errors += 1
    else:
        monitor.success_counts[function_name] += 1
