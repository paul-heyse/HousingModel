## 1. Inventory & Plan
- [x] 1.1 Search for all `marshmallow` imports and schema definitions
- [x] 1.2 Classify each usage as domain/config (Pydantic) or DataFrame (Pandera)

## 2. Migration
- [x] 2.1 Create Pydantic models replacing Marshmallow domain/config schemas
- [x] 2.2 Create Pandera schemas for tabular validations (if any were using Marshmallow)
- [x] 2.3 Update validation adapters/utilities to use Pydantic/Pandera only
- [x] 2.4 Replace references in flows/services; adapt error handling

## 3. Dependencies & Cleanup
- [x] 3.1 Remove `marshmallow` from base dependencies
- [x] 3.2 Ensure `py.typed` present in packages exposing models
- [x] 3.3 Update docs/examples

## 4. Tests & DoD
- [x] 4.1 Update tests for new models and validations
- [x] 4.2 Parity tests for key schemas (old vs new) where practical
- [x] 4.3 CI green: ruff, black, pytest
- [x] 4.4 Spec validation: `openspec validate --strict`

