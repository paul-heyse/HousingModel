from pathlib import Path

import pytest
from pydantic import ValidationError

from aker_core.config import Settings, build_run_config, reset_settings_cache
from aker_core.flags import current_flag_state, is_enabled


@pytest.fixture(autouse=True)
def clear_settings_cache():
    reset_settings_cache()
    yield
    reset_settings_cache()


def test_environment_overrides_dotenv(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    env_file = tmp_path / ".env"
    env_file.write_text("AKER_POSTGIS_DSN=postgresql://dotenv\n", encoding="utf-8")

    monkeypatch.setenv("AKER_POSTGIS_DSN", "postgresql://env")

    settings = Settings(_env_file=env_file)

    assert settings.postgis_dsn.get_secret_value() == "postgresql://env"
    assert settings.source_for("postgis_dsn") == "env"


def test_dotenv_overrides_defaults(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    env_file = tmp_path / ".env"
    env_file.write_text(
        "AKER_POSTGIS_DSN=postgresql://dotenv\nAKER_PREFECT_API_URL=https://dotenv.prefect/api\n",
        encoding="utf-8",
    )
    monkeypatch.delenv("AKER_PREFECT_API_URL", raising=False)
    monkeypatch.delenv("AKER_POSTGIS_DSN", raising=False)

    settings = Settings(_env_file=env_file)

    assert str(settings.prefect_api_url) == "https://dotenv.prefect/api"
    assert settings.source_for("prefect_api_url") == "dotenv"


def test_snapshot_excludes_secrets(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("AKER_POSTGIS_DSN", "postgresql://env")
    monkeypatch.delenv("AKER_CENSUS_API_KEY", raising=False)
    settings = Settings()

    snapshot = settings.snapshot()

    assert "postgis_dsn" not in snapshot
    assert snapshot["feature_flags"]["ETL_OSRM"] is False


def test_feature_flag_env_override(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    env_file = tmp_path / ".env"
    env_file.write_text("AKER_POSTGIS_DSN=postgresql://dotenv\n", encoding="utf-8")

    monkeypatch.setenv("AKER_FEATURE_FLAGS__ETL_OSRM", "true")

    settings = Settings(_env_file=env_file)

    assert is_enabled("ETL_OSRM", settings=settings) is True
    assert current_flag_state(settings)["ETL_OSRM"] is True


def test_missing_required_dependency_raises(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("AKER_POSTGIS_DSN", raising=False)
    with pytest.raises(ValidationError):
        Settings()


def test_optional_dependency_defaults(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("AKER_POSTGIS_DSN", "postgresql://env")
    monkeypatch.delenv("AKER_PREFECT_API_URL", raising=False)

    settings = Settings()

    assert settings.prefect_api_url is None


def test_run_config_echoes_feature_flags(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("AKER_POSTGIS_DSN", "postgresql://env")
    monkeypatch.setenv("AKER_FEATURE_FLAGS__ETL_OSRM", "true")

    config = build_run_config(Settings())

    assert config["feature_flags"]["ETL_OSRM"] is True


def test_snapshot_hash_stability(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("AKER_POSTGIS_DSN", "postgresql://env")
    settings = Settings()

    snapshot_one = settings.snapshot()
    snapshot_two = settings.snapshot()

    assert snapshot_one == snapshot_two


def test_build_run_config_without_explicit_settings(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("AKER_POSTGIS_DSN", "postgresql://env")
    monkeypatch.delenv("AKER_FEATURE_FLAGS__ETL_OSRM", raising=False)

    reset_settings_cache()
    config = build_run_config()

    assert config["environment"] == "development"
    assert config["feature_flags"]["ETL_OSRM"] is False


def test_feature_flag_invalid_value(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("AKER_POSTGIS_DSN", "postgresql://env")
    monkeypatch.setenv("AKER_FEATURE_FLAGS__ETL_OSRM", "not-a-bool")

    with pytest.raises(ValidationError):
        Settings()


def test_feature_flag_unknown_ignored(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("AKER_POSTGIS_DSN", "postgresql://env")
    monkeypatch.setenv("AKER_FEATURE_FLAGS__UNKNOWN_FLAG", "true")

    settings = Settings()

    assert "UNKNOWN_FLAG" not in settings.feature_flag_map()


def test_sources_snapshot(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    env_file = tmp_path / ".env"
    env_file.write_text("AKER_PREFECT_API_URL=https://dotenv.prefect/api\n", encoding="utf-8")

    monkeypatch.setenv("AKER_POSTGIS_DSN", "postgresql://env")
    monkeypatch.delenv("AKER_FEATURE_FLAGS__ETL_OSRM", raising=False)

    settings = Settings(_env_file=env_file)

    assert settings.sources == {
        "environment": "default",
        "postgis_dsn": "env",
        "prefect_api_url": "dotenv",
        "osrm_base_url": "default",
        "census_api_key": "default",
        "bls_api_key": "default",
        "great_expectations_root": "default",
        "feature_flags": "default",
    }


def test_optional_fields_default_safely(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("AKER_POSTGIS_DSN", "postgresql://env")

    settings = Settings()

    assert settings.prefect_api_url is None
    assert str(settings.osrm_base_url) == "https://router.project-osrm.org/"
    assert settings.census_api_key is None
    assert settings.bls_api_key is None
    assert settings.great_expectations_root is None
