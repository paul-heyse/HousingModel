"""Feature flag helper functions."""

from __future__ import annotations

from typing import Dict

from .config import Settings, build_run_config, get_settings


def is_enabled(flag_name: str, *, settings: Settings | None = None) -> bool:
    runtime_settings = settings or get_settings()
    flags = runtime_settings.feature_flag_map()
    return flags.get(flag_name.upper(), False)


def current_flag_state(settings: Settings | None = None) -> Dict[str, bool]:
    runtime_settings = settings or get_settings()
    return runtime_settings.feature_flag_map().copy()


__all__ = ["is_enabled", "current_flag_state", "build_run_config"]
