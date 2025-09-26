## Why
The platform needs a single source of truth for runtime configuration that obeys 12-factor principles. Analysts and services must be able to toggle capabilities without code changes while keeping secrets out of the repository.

## What Changes
- Introduce a `aker_core.config.Settings` Pydantic v2 settings object that merges defaults, optional `.env`, and environment variables.
- Add a lightweight feature-flag helper `aker_core.flags.is_enabled()` backed by the settings module and captured in run metadata.
- Document precedence rules and acceptance tests covering environment > `.env` > defaults with snapshots of the resolved configuration.

## Impact
- Affected specs: core/configuration
- Affected code: `src/aker_core/config.py`, `src/aker_core/flags.py`, relevant tests and run metadata writers.
