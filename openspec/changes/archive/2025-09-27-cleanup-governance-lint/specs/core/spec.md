## ADDED Requirements
### Requirement: Governance Package Lint Compliance
The governance module and its associated tests SHALL pass default linting rules (import order, unused symbol elimination) so that `ruff check .` can be relied on for regressions without local overrides.

#### Scenario: Governance Imports Organized
- **WHEN** `ruff check` runs against `src/aker_core/governance` and governance-related tests
- **THEN** it SHALL succeed without unsorted-import (`I001`) or unused-import (`F401`) reports.

### Requirement: Demo/Test Isolation Strategy Documented
Legacy governance demos or long-running scripts SHALL either comply with lint rules or live in a clearly documented location that is excluded from production linting, preventing continuous baseline noise.

#### Scenario: Lint Baseline Remains Clean After Demo Changes
- **WHEN** a new developer runs `ruff check .`
- **THEN** governance-related demo/test files SHALL not introduce non-actionable lint failures because they are either clean or explicitly excluded with justification in the lint configuration.
