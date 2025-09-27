## ADDED Requirements
### Requirement: Regulatory Friction Encoders
The market scoring system SHALL expose `aker_market.regulatory.encode_rules(text_or_tables) -> dict[str, int | bool]` that normalizes municipal regulatory signals covering zoning, inclusionary zoning (IZ), design review, height/FAR envelope controls, parking minimum strictness, and water moratoria. The returned dictionary SHALL include the keys `iz_flag`, `review_flag`, `height_idx`, `parking_idx`, and `water_moratorium_flag`, where indices (e.g., `height_idx` representing combined height/FAR envelope strictness) are bounded integers with `0` signifying least restrictive and flags are booleans suitable for scorecard ingestion. The encoder SHALL document provenance for each mapping and persist outputs to storage columns with the same names so downstream scoring, analytics, and exports can rely on consistent schema.

#### Scenario: Fixture City Encodings Match Manual Truth Set
- **GIVEN** a fixture dataset describing Portland, Denver, and Phoenix regulatory rules curated in the manual truth set
- **WHEN** `encode_rules` ingests the associated narrative text and structured tables
- **THEN** the resulting dictionary for each city SHALL equal the stored truth values for `iz_flag`, `review_flag`, `height_idx`, `parking_idx`, and `water_moratorium_flag` and persist the same values into the regulatory schema

#### Scenario: Missing Signals Produce Safe Defaults
- **GIVEN** an input document that omits design review or height information
- **WHEN** `encode_rules` processes the record
- **THEN** the encoder SHALL default indices to zero, flags to `False`, and record the absence in provenance so downstream metrics remain deterministic
