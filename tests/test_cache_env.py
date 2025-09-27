from __future__ import annotations

import json
import tempfile
from pathlib import Path

import pandas as pd

from aker_core.cache import Cache


def test_cache_base_path_env_override(monkeypatch: pytest.MonkeyPatch) -> None:
    with tempfile.TemporaryDirectory() as tmpdir:
        override_path = Path(tmpdir) / "custom_cache"
        monkeypatch.setenv("AKER_CACHE_PATH", str(override_path))

        cache = Cache(base_path=None)
        assert cache.base_path == override_path

        df = pd.DataFrame({"id": [1], "value": [2]})

        stored = cache.store_local(df, "dataset", "data.parquet", data_type="parquet")
        stored_path = Path(stored)
        assert stored_path.is_file()
        assert stored_path.parents[2] == override_path


def test_cache_json_storage_metadata(tmp_path: Path) -> None:
    cache = Cache(base_path=tmp_path)
    payload = {"key": "value", "nested": {"a": 1}}

    stored = cache.store_local(payload, "json_dataset", "config.json")
    stored_path = Path(stored)
    assert stored_path.suffix == ".json"
    with open(stored_path, "r", encoding="utf-8") as f:
        assert json.load(f) == payload

    metadata = Cache.read_metadata(stored_path)
    assert metadata["data_type"] == "json"
    assert metadata["original_filename"] == "config.json"
