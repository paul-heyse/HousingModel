## Why
Our `ruff check` pass still fails because large swaths of governance code, tests, and demos are littered with unsorted imports, unused symbols, and legacy scaffolding. These violations hide real lint failures and make automation noisy. We already chipped away at geospatial debt; now we need a focused cleanup of the governance surface so baseline linting is meaningful again.

## What Changes
- Normalize imports and remove unused symbols across the governance package (`src/aker_core/governance/**`, related database modules, and their tests).
- Fix or quarantine legacy governance demos/tests that can't meet lint standards by default (e.g., move to `examples/` or add precise `per-file-ignores`).
- Update `pyproject.toml` if needed (per-file ignores or additional excludes) with clear documentation, ensuring `ruff check .` runs clean without masking genuine regressions.

## Impact
- Affected specs: core (governance operations and developer hygiene)
- Affected code: Governance modules & tests, lint configuration (`pyproject.toml`).
