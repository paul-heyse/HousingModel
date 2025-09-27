"""Runtime configuration surface for the Aker Platform.

The module wraps `pydantic-settings` to give the application a single place to
resolve configuration in 12-factor precedence (environment > dotenv > defaults).
Secrets never appear in exported snapshots and feature flags are exposed in a
way that downstream services can persist alongside run metadata.
"""

from __future__ import annotations

import os
from functools import lru_cache
from pathlib import Path
from typing import Any, Dict, Iterable, Literal

from pydantic import BaseModel, ConfigDict, Field, PrivateAttr, SecretStr

try:
    from pydantic import AnyHttpUrl
except ImportError:
    # Fallback for older pydantic versions
    from pydantic.networks import HttpUrl as AnyHttpUrl
from pydantic_settings import BaseSettings, SettingsConfigDict

Source = Literal["env", "dotenv", "default"]


def _normalise_key(key: str) -> str:
    return key.strip().upper()


def _read_env_file(path: str | os.PathLike[str] | None) -> Dict[str, str]:
    if path is None:
        return {}

    env_path = Path(path)
    if not env_path.is_absolute():
        env_path = Path.cwd() / env_path

    if not env_path.exists():
        return {}

    values: Dict[str, str] = {}
    for line in env_path.read_text(encoding="utf-8").splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        if "=" not in stripped:
            continue
        key, value = stripped.split("=", 1)
        values[_normalise_key(key)] = value.strip().strip('"').strip("'")
    return values


class FeatureFlags(BaseModel):
    """Typed feature toggles exposed to application code."""

    model_config = ConfigDict(populate_by_name=True, extra="ignore")

    etl_osrm: bool = Field(default=False, alias="ETL_OSRM")

    def as_dict(self) -> Dict[str, bool]:
        return {"ETL_OSRM": self.etl_osrm}


class Settings(BaseSettings):
    """Centralised runtime configuration for the platform."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        env_prefix="AKER_",
        env_nested_delimiter="__",
        case_sensitive=False,
        extra="ignore",
    )

    environment: str = Field(default="development")
    postgis_dsn: SecretStr
    prefect_api_url: AnyHttpUrl | None = Field(default=None)
    osrm_base_url: AnyHttpUrl = Field(default="https://router.project-osrm.org/")
    census_api_key: SecretStr | None = Field(default=None)
    bls_api_key: SecretStr | None = Field(default=None)
    great_expectations_root: str | None = Field(default=None)
    feature_flags: FeatureFlags = Field(default_factory=FeatureFlags)

    _source_map: Dict[str, Source] = PrivateAttr(default_factory=dict)
    _env_file_override: str | None = PrivateAttr(default=None)

    def __init__(
        self, *args: Any, _env_file: str | os.PathLike[str] | None = None, **kwargs: Any
    ) -> None:
        super().__init__(*args, _env_file=_env_file, **kwargs)
        object.__setattr__(
            self, "_env_file_override", str(_env_file) if _env_file is not None else None
        )
        object.__setattr__(self, "_source_map", self._build_source_map())

    def model_post_init(self, __context: Any) -> None:  # pragma: no cover - exercised indirectly
        super().model_post_init(__context)
        object.__setattr__(self, "_source_map", self._build_source_map())

    @property
    def sources(self) -> Dict[str, Source]:
        return self._source_map.copy()

    def source_for(self, field: str) -> Source:
        return self._source_map.get(field, "default")

    def feature_flag_map(self) -> Dict[str, bool]:
        return self.feature_flags.as_dict()

    def snapshot(self) -> Dict[str, Any]:
        def scrub(item: Any) -> Any:
            if isinstance(item, SecretStr):
                return None
            if isinstance(item, BaseModel):
                return {
                    key: scrub(value)
                    for key, value in item.model_dump(mode="json").items()
                    if not isinstance(value, SecretStr)
                }
            if isinstance(item, dict):
                return {key: scrub(value) for key, value in item.items()}
            if isinstance(item, list):
                return [scrub(value) for value in item]
            return item

        json_data = self.model_dump(mode="json")
        raw_data = self.model_dump()

        result: Dict[str, Any] = {}
        for key, value in json_data.items():
            raw_value = raw_data.get(key)
            if isinstance(raw_value, SecretStr):
                continue
            scrubbed = scrub(value)
            result[key] = scrubbed
        if "feature_flags" in result:
            result["feature_flags"] = self.feature_flag_map()
        return result

    def run_config_payload(self) -> Dict[str, Any]:
        payload = self.snapshot()
        payload["feature_flags"] = self.feature_flag_map()
        return payload

    def _build_source_map(self) -> Dict[str, Source]:
        env_prefix = (self.model_config.get("env_prefix") or "").upper()
        env_snapshot = {key.upper(): value for key, value in os.environ.items()}
        env_file_obj = self._env_file_override or self.model_config.get("env_file")
        # pydantic may allow a sequence of env files; pick the first for source mapping
        if isinstance(env_file_obj, (list, tuple)):
            env_file_val = env_file_obj[0] if env_file_obj else None
        else:
            env_file_val = env_file_obj
        dotenv_values = _read_env_file(env_file_val)

        def from_env(keys: Iterable[str]) -> bool:
            for candidate in keys:
                upper = candidate.upper()
                if upper in env_snapshot:
                    return True
                if any(name.startswith(f"{upper}__") for name in env_snapshot):
                    return True
            return False

        def from_dotenv(keys: Iterable[str]) -> bool:
            for candidate in keys:
                upper = candidate.upper()
                if upper in dotenv_values:
                    return True
                if any(name.startswith(f"{upper}__") for name in dotenv_values):
                    return True
            return False

        source_map: Dict[str, Source] = {}
        for name, field in self.__class__.model_fields.items():
            alias = field.alias or name
            candidates = [alias]
            if env_prefix:
                candidates.append(f"{env_prefix}{alias}")
            if from_env(candidates):
                source_map[name] = "env"
            elif from_dotenv(candidates):
                source_map[name] = "dotenv"
            else:
                source_map[name] = "default"
        return source_map


@lru_cache(maxsize=1)
def get_settings(*, _env_file: str | os.PathLike[str] | None = None) -> Settings:
    return Settings(_env_file=_env_file)


def reset_settings_cache() -> None:
    get_settings.cache_clear()


def build_run_config(settings: Settings | None = None) -> Dict[str, Any]:
    runtime_settings = settings or get_settings()
    config = runtime_settings.run_config_payload()
    config["feature_flags"] = runtime_settings.feature_flag_map()
    return config
