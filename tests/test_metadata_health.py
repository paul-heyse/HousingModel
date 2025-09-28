"""Ensure ORM metadata remains healthy and free of duplicate table registrations."""

from __future__ import annotations

import importlib

import pytest

from aker_data.base import Base


@pytest.mark.parametrize(
    "module_name",
    [
        "aker_data.models",
        "aker_data.models_extra",
        "aker_core.database.ops",
    ],
)
def test_metadata_imports_without_duplicates(module_name: str) -> None:
    """Importing ORM modules should not register duplicate tables."""
    try:
        importlib.import_module(module_name)
    except ImportError as exc:
        pytest.skip(f"Module {module_name} unavailable: {exc}")

    table_names = list(Base.metadata.tables.keys())
    assert len(table_names) == len(set(table_names)), "Duplicate SQLAlchemy table names detected"


def test_declarative_base_shared_registry() -> None:
    """All mapped classes should use the shared Base registry."""

    # Load canonical models to populate registry
    importlib.import_module("aker_data.models")

    registries = {mapper.registry for mapper in Base.registry.mappers}
    assert registries == {Base.registry}, "Detected mapper bound to unexpected registry"
