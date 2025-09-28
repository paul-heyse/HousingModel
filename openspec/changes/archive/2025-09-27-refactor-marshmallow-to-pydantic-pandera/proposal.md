## Why
Marshmallow usage is minimal and overlaps with Pydantic (for domain/config validation) and Pandera (for DataFrame validation). Consolidating on Pydantic+Pandera reduces dependency weight, improves typing, and simplifies maintenance. Great Expectations deprecation has already concluded and is out of scope.

## What Changes
- Inventory all Marshmallow schemas/usages.
- Replace Marshmallow with:
  - Pydantic models for domain objects, config, and request/response validation.
  - Pandera schemas for tabular (DataFrame) validation.
- Update flows and services to use consolidated validators.
- Remove Marshmallow from base dependencies.

## Impact
- Affected specs: `core` (validation policy only)
- Affected code: modules referencing Marshmallow; validation helpers; tests
- Dependencies: remove `marshmallow` after migration

## Non-Goals
- No consolidation of `aker_core` and `aker_deal` libraries in this change.
- No additional changes to Great Expectations (already completed elsewhere).

## Risks / Mitigations
- Risk: Subtle behavior differences in serialization/validation → Parity tests and staged rollout.
- Risk: Custom Marshmallow fields/validators → Implement equivalent Pydantic validators or Pandera checks.

