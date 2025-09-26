"""Plugin registry supporting hexagonal adapters."""

from __future__ import annotations

from collections.abc import Callable, Iterable
from contextlib import contextmanager
from importlib import metadata
from typing import Any, Dict, Iterator

PluginFactory = Callable[[], Any]

_PLUGIN_GROUP = "aker_core.plugins"
_REGISTRY: Dict[str, PluginFactory] = {}

PLUGIN_GROUP = _PLUGIN_GROUP


def _normalise(name: str) -> str:
    return name.strip().lower()


def register(name: str, factory: PluginFactory, *, override: bool = False) -> None:
    key = _normalise(name)
    if not override and key in _REGISTRY:
        raise ValueError(f"Plugin '{name}' already registered")
    _REGISTRY[key] = factory


def get(name: str) -> PluginFactory:
    key = _normalise(name)
    try:
        return _REGISTRY[key]
    except KeyError as exc:  # pragma: no cover - defensive
        raise KeyError(f"Plugin '{name}' is not registered") from exc


def unregister(name: str) -> None:
    _REGISTRY.pop(_normalise(name), None)


def available() -> Dict[str, PluginFactory]:
    return dict(_REGISTRY)


def discover(*, group: str = _PLUGIN_GROUP, override: bool = False) -> None:
    eps = metadata.entry_points()
    entries: Iterable[Any]
    if hasattr(eps, "select"):
        entries = eps.select(group=group)
    else:  # pragma: no cover - compatibility for <3.10
        entries = eps.get(group, [])  # type: ignore[arg-type]

    for entry in entries:
        factory = entry.load()
        register(entry.name, factory, override=override)


@contextmanager
def override(name: str, factory: PluginFactory) -> Iterator[None]:
    key = _normalise(name)
    original = _REGISTRY.get(key)
    register(name, factory, override=True)
    try:
        yield
    finally:
        if original is not None:
            _REGISTRY[key] = original
        else:
            _REGISTRY.pop(key, None)


def clear() -> None:
    _REGISTRY.clear()


__all__ = [
    "register",
    "get",
    "unregister",
    "available",
    "discover",
    "override",
    "clear",
    "PLUGIN_GROUP",
]
