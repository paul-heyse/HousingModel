from __future__ import annotations

from dataclasses import dataclass
from typing import Callable

import pytest

import aker_core.plugins as plugins


@pytest.fixture(autouse=True)
def reset_registry():
    plugins.clear()
    yield
    plugins.clear()


@dataclass
class StubConnector:
    name: str = "stub"

    def run(self) -> str:
        return self.name


def stub_factory(name: str) -> Callable[[], StubConnector]:
    def factory() -> StubConnector:
        return StubConnector(name=name)

    return factory


def test_register_and_get_returns_factory():
    plugins.register("census_acs", stub_factory("census"))

    factory = plugins.get("census_acs")
    instance = factory()

    assert isinstance(instance, StubConnector)
    assert instance.name == "census"


def test_register_duplicate_without_override_raises():
    plugins.register("census_acs", stub_factory("one"))
    with pytest.raises(ValueError):
        plugins.register("census_acs", stub_factory("two"))


def test_unregister_removes_plugin():
    plugins.register("census_acs", stub_factory("one"))
    plugins.unregister("census_acs")

    with pytest.raises(KeyError):
        plugins.get("census_acs")


def test_override_context_restores_previous_registration():
    plugins.register("census_acs", stub_factory("prod"))

    with plugins.override("census_acs", stub_factory("test")):
        assert plugins.get("census_acs")().name == "test"

    assert plugins.get("census_acs")().name == "prod"


def test_discover_loads_entry_points(monkeypatch: pytest.MonkeyPatch) -> None:
    class FakeEntryPoint:
        def __init__(self, name: str, factory: Callable[[], StubConnector]):
            self.name = name
            self._factory = factory

        def load(self) -> Callable[[], StubConnector]:
            return self._factory

    class FakeEntryPoints(list):
        def select(self, *, group: str):
            if group == plugins.PLUGIN_GROUP:
                return self
            return []

    fake_eps = FakeEntryPoints(
        [
            FakeEntryPoint("census_acs", stub_factory("discover")),
            FakeEntryPoint("osmnx", stub_factory("osmnx")),
        ]
    )

    monkeypatch.setattr(plugins.metadata, "entry_points", lambda: fake_eps)

    plugins.discover()

    names = {name: factory().name for name, factory in plugins.available().items()}
    assert names == {"census_acs": "discover", "osmnx": "osmnx"}


def test_discover_with_custom_group(monkeypatch: pytest.MonkeyPatch) -> None:
    class FakeEntryPoint:
        def __init__(self, name: str, factory: Callable[[], StubConnector]):
            self.name = name
            self._factory = factory

        def load(self) -> Callable[[], StubConnector]:
            return self._factory

    class FakeEntryPoints(list):
        def select(self, *, group: str):
            if group == "custom.group":
                return self
            return []

    fake_eps = FakeEntryPoints([FakeEntryPoint("custom", stub_factory("custom"))])
    monkeypatch.setattr(plugins.metadata, "entry_points", lambda: fake_eps)

    plugins.discover(group="custom.group")

    assert plugins.get("custom")().name == "custom"
