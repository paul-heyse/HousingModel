## 1. Governance Imports & Unused Symbols
- [x] 1.1 Run `ruff check src/aker_core/governance src/aker_core/database/governance tests/test_governance*.py --fix` to auto-clean where possible.
- [x] 1.2 Manually resolve remaining unused imports/functions, deleting dead code or wiring up missing references.

## 2. Demo/Test Quarantine
- [x] 2.1 Identify governance demos/tests that cannot meet lint rules; move them to an `examples/` directory or add targeted `per-file-ignores` with justification.

## 3. Lint Baseline
- [x] 3.1 Update `pyproject.toml` exclusions/notes as needed and confirm `ruff check .` passes.
