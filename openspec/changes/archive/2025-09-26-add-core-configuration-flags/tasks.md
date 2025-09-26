## 1. Implementation
- [x] 1.1 Create `aker_core.config.Settings` with typed fields for all external services and feature flags, loaded via pydantic-settings.
- [x] 1.2 Provide helpers for loading settings and `aker_core.flags.is_enabled("<flag>")`, ensuring flag states are included in `runs.config_json`.
- [x] 1.3 Write unit tests covering precedence (env > .env > defaults) and snapshot the resolved configuration structure.
- [x] 1.4 Update developer docs/examples to illustrate environment-first configuration and flag usage.
