## ADDED Requirements

### Requirement: Consolidate Validation on Pydantic and Pandera
The system SHALL use Pydantic for domain/config validation and Pandera for DataFrame validation; Marshmallow SHALL NOT be used.

#### Scenario: Domain/config via Pydantic
- **WHEN** application code needs to validate/serialize domain or configuration objects
- **THEN** Pydantic models are used with type-annotated fields and validators

#### Scenario: Tabular data via Pandera
- **WHEN** flows/services validate pandas DataFrames
- **THEN** Pandera schemas are applied and violations reported with structured errors

## REMOVED Requirements

### Requirement: Marshmallow Schemas
**Reason**: Overlap with Pydantic; consolidation improves type safety and reduces dependencies.
**Migration**: Implement equivalent Pydantic models and Pandera schemas.

