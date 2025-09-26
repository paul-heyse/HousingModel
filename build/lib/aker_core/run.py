"""Run context management for deterministic pipeline executions."""

from __future__ import annotations

import hashlib
import json
import os
import random
import subprocess
from contextlib import AbstractContextManager
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Callable, Optional

from sqlalchemy.orm import Session

from aker_core.config import Settings, get_settings
from aker_data.models import Lineage, Runs

SessionFactory = Callable[[], Session]


def _detect_git_sha() -> str:
    env_sha = os.environ.get("GIT_SHA") or os.environ.get("GITHUB_SHA")
    if env_sha:
        return env_sha[:40]
    try:
        result = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            check=True,
            capture_output=True,
            text=True,
        )
        return result.stdout.strip()[:40]
    except Exception:  # pragma: no cover - fallback when git unavailable
        return "unknown"


def _hash_snapshot(snapshot: dict[str, Any]) -> str:
    payload = json.dumps(snapshot, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def _derive_seed(config_hash: str) -> int:
    return int(config_hash[:16], 16) % (2**32)


def _apply_seed(seed: int) -> None:
    random.seed(seed)
    try:  # pragma: no cover - numpy optional dependency
        import numpy as np

        np.random.seed(seed)
    except Exception:
        pass


@dataclass
class RunContextState:
    run_id: int
    git_sha: str
    config_hash: str
    seed: int
    started_at: datetime
    finished_at: Optional[datetime]
    config_snapshot: dict[str, Any]


class RunContext(AbstractContextManager["RunContext"]):
    """Context manager encapsulating a single deterministic pipeline run."""

    def __init__(
        self,
        session_factory: SessionFactory,
        *,
        settings: Optional[Settings] = None,
        git_sha: Optional[str] = None,
        seed: Optional[int] = None,
    ) -> None:
        self._session_factory = session_factory
        self._provided_settings = settings
        self._provided_git_sha = git_sha
        self._provided_seed = seed
        self._run_record: Runs | None = None
        self._meta_session: Session | None = None
        self._data_session: Session | None = None
        self._config_snapshot: dict[str, Any] | None = None
        self._config_hash: str | None = None
        self._seed: int | None = None
        self._git_sha: str | None = None
        self._state: RunContextState | None = None
        self._active = False
        self._output_hash: str | None = None
        self._rng: random.Random | None = None

    # Public properties -------------------------------------------------

    @property
    def session(self) -> Session:
        if not self._active or self._data_session is None:
            raise RuntimeError("RunContext session requested outside active context")
        return self._data_session

    @property
    def id(self) -> int:
        if not self._state:
            raise RuntimeError("RunContext has not been entered")
        return self._state.run_id

    @property
    def git_sha(self) -> str:
        if not self._state:
            raise RuntimeError("RunContext has not been entered")
        return self._state.git_sha

    @property
    def config_hash(self) -> str:
        if not self._state:
            raise RuntimeError("RunContext has not been entered")
        return self._state.config_hash

    @property
    def seed(self) -> int:
        if not self._state:
            raise RuntimeError("RunContext has not been entered")
        return self._state.seed

    @property
    def rng(self) -> random.Random:
        if not self._state:
            raise RuntimeError("RunContext has not been entered")
        if self._rng is None:
            self._rng = random.Random(self._state.seed)
        return self._rng

    @property
    def started_at(self) -> datetime:
        if not self._state:
            raise RuntimeError("RunContext has not been entered")
        return self._state.started_at

    @property
    def finished_at(self) -> Optional[datetime]:
        if not self._state:
            return None
        return self._state.finished_at

    # Context management -----------------------------------------------

    def __enter__(self) -> "RunContext":
        self._meta_session = self._session_factory()
        settings = self._provided_settings or get_settings()
        self._config_snapshot = settings.snapshot()
        self._config_hash = _hash_snapshot(self._config_snapshot)
        self._git_sha = (self._provided_git_sha or _detect_git_sha())[:40]
        self._seed = (
            self._provided_seed
            if self._provided_seed is not None
            else _derive_seed(self._config_hash)
        )
        _apply_seed(self._seed)
        self._rng = random.Random(self._seed)

        started_at = datetime.now(timezone.utc)
        run = Runs(
            git_sha=self._git_sha,
            config_hash=self._config_hash,
            config_json=self._config_snapshot,
            seed=self._seed,
            started_at=started_at,
            status="running",
        )
        self._meta_session.add(run)
        self._meta_session.commit()
        self._run_record = run
        self._state = RunContextState(
            run_id=run.run_id,
            git_sha=self._git_sha,
            config_hash=self._config_hash,
            seed=self._seed,
            started_at=started_at,
            finished_at=None,
            config_snapshot=self._config_snapshot,
        )
        self._data_session = self._session_factory()
        self._active = True
        return self

    def __exit__(self, exc_type, exc, tb) -> bool:
        if not self._active:
            return False
        finished_at = datetime.now(timezone.utc)
        success = exc_type is None

        if self._data_session is not None:
            if success:
                self._data_session.commit()
            else:
                self._data_session.rollback()
            self._data_session.close()
            self._data_session = None

        if self._meta_session is not None and self._run_record is not None:
            run = self._meta_session.get(Runs, self._run_record.run_id)
            if run is not None:
                run.finished_at = finished_at
                run.output_hash = self._output_hash
                run.status = "completed" if success else "failed"
                if run.config_hash is None:
                    run.config_hash = self._config_hash or ""
                self._meta_session.commit()
            self._meta_session.close()
            self._meta_session = None

        if self._state:
            self._state.finished_at = finished_at

        self._active = False
        return False  # do not suppress exceptions

    # API ---------------------------------------------------------------

    def log_lineage(
        self,
        table: str,
        source: str,
        url: Optional[str],
        fetched_at: datetime,
        hash_value: str,
    ) -> None:
        if not self._active or self._meta_session is None or not self._state:
            raise RuntimeError("log_lineage requires an active RunContext")
        lineage = Lineage(
            run_id=self._state.run_id,
            table=table,
            source=source,
            source_url=url,
            fetched_at=fetched_at,
            hash=hash_value,
        )
        self._meta_session.add(lineage)
        self._meta_session.commit()

    def log_data_lake_operation(
        self,
        operation: str,
        dataset: str,
        path: str,
        metadata: Optional[dict[str, Any]] = None,
    ) -> None:
        """Log data lake operations to lineage table.

        Args:
            operation: Operation type ('write', 'read', etc.)
            dataset: Dataset name
            path: File path or partition path
            metadata: Additional metadata (optional)
        """
        if not self._active or self._meta_session is None or not self._state:
            raise RuntimeError("log_data_lake_operation requires an active RunContext")

        # Create a hash of the operation details for lineage tracking
        operation_data = {
            "operation": operation,
            "dataset": dataset,
            "path": path,
            "run_id": self._state.run_id,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "metadata": metadata or {},
        }
        operation_hash = hashlib.sha256(
            json.dumps(operation_data, sort_keys=True, separators=(",", ":")).encode("utf-8")
        ).hexdigest()

        lineage = Lineage(
            run_id=self._state.run_id,
            table=f"data_lake:{dataset}",
            source=f"data_lake:{operation}",
            source_url=path,
            fetched_at=datetime.now(timezone.utc),
            hash=operation_hash,
        )
        self._meta_session.add(lineage)
        self._meta_session.commit()

    def set_output_hash(self, output_hash: str) -> None:
        if not self._active:
            raise RuntimeError("set_output_hash requires an active RunContext")
        self._output_hash = output_hash

    def state(self) -> RunContextState:
        if not self._state:
            raise RuntimeError("RunContext has not been entered")
        return self._state


__all__ = ["RunContext", "RunContextState"]
