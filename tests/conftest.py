from __future__ import annotations

import base64
from pathlib import Path

import pytest

PNG_DATA = base64.b64decode(
    "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mP8/x8AAoMBgI/WMxwAAAAASUVORK5CYII="
)


def _write_image(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(PNG_DATA)


@pytest.fixture
def image_payload(tmp_path: Path) -> dict[str, str]:
    images_dir = tmp_path / "images"
    images_dir.mkdir(exist_ok=True)
    payload: dict[str, str] = {}
    for stem in ("pillar_bars", "urban_isochrone", "roi_ladder"):
        image_path = images_dir / f"{stem}.png"
        _write_image(image_path)
        payload[stem] = str(image_path)
    return payload
