## 1. Specification
- [x] 1.1 Define ORM metadata governance and lint guardrail requirements in the `core` delta.
- [x] 1.2 Outline acceptance tests (unit + CI hooks) that prove the new requirements.
- [x] 1.3 Validate change with `openspec validate refactor-orm-metadata-lint-guardrails --strict`.

## 2. Implementation Planning
- [x] 2.1 Inventory all declarative bases/metadata instances and propose a single registry migration plan.
- [x] 2.2 Document lint backlog triage, automation updates (pre-commit/CI), and developer workflow adjustments.
- [x] 2.3 Sequence refactor by module, including migration/testing strategy to avoid runtime regressions.

## 3. Follow-up
- [x] 3.1 Coordinate with platform owners to schedule the metadata migration window and communicate lint policy changes.
