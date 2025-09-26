"""Data layer package: SQLAlchemy base, models, DB helpers, and data lake."""

from __future__ import annotations

from .base import Base, metadata
from .lake import DataLake

# Note: Users should create their own DataLake instance with appropriate base_path
# lake = DataLake()  # Uncomment and set base_path as needed

__all__ = ["Base", "metadata", "DataLake"]
