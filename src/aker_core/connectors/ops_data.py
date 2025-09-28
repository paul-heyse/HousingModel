from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Iterable, Mapping


@dataclass(frozen=True)
class Review:
    rating: float
    text: str
    created_at: datetime
    source: str
    weight: float = 1.0


class ReviewsConnector:
    def fetch(self, *, asset_id: int) -> Iterable[Mapping[str, float | int | str]]:
        raise NotImplementedError


class NPSConnector:
    def fetch(self, *, asset_id: int) -> float:
        raise NotImplementedError


