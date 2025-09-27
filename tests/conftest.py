"""Pytest configuration ensuring local sources are importable."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent
SRC_PATH = ROOT_DIR / "src"
if SRC_PATH.exists() and str(SRC_PATH) not in sys.path:
    sys.path.insert(0, str(SRC_PATH))


def pytest_ignore_collect(collection_path: Path, config):  # pragma: no cover - test harness utility
    """Skip vendored GDAL autotests that require compiled GDAL bindings."""

    return "gdal/autotest" in str(collection_path)
