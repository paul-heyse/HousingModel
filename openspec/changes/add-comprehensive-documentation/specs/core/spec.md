## ADDED Requirements
### Requirement: Core Modules Expose Intent Through Docstrings
Core packages SHALL provide module, class, and function docstrings that summarize purpose, critical dependencies, and interactions so developers and analysts can map specs to implementation quickly.

#### Scenario: Public API Docstrings Explain Objective and Usage
- **WHEN** a public module, class, or function is created or modified under `src/`
- **THEN** its docstring SHALL describe the business objective it supports, key inputs and outputs, and links or references to the relevant knowledge base entry or spec requirement
- **AND** docstrings SHALL surface non-obvious side effects, invariants, or performance considerations consumers must respect
- **AND** linting or CI SHALL fail when public surfaces lack required docstrings

#### Scenario: Module Headers Map Specs to Code
- **WHEN** a package or module initializes capability-specific logic (e.g., `src/aker_market/`)
- **THEN** the top-level docstring SHALL enumerate the primary specs it implements, highlight orchestrating entry points, and note integration points with external services or datasets
- **AND** onboarding developers SHALL be able to trace from the module header to concrete implementation files without external guidance

### Requirement: Inline Commentary Captures Design Rationale
The codebase SHALL include concise inline commentary where implementations encode domain heuristics, data quirks, or non-obvious algorithms so maintainers understand the intent behind the logic.

#### Scenario: Complex Logic Annotated With Rationale
- **WHEN** code introduces algorithmic shortcuts, domain adjustments, or data-cleansing heuristics that are not self-evident
- **THEN** inline comments SHALL explain the purpose of the adjustment, expected bounds, and references to supporting analysis or data sources
- **AND** comments SHALL stay synchronized with behavior by being reviewed during code changes
- **AND** reviewers SHALL request updates when logic diverges from documented rationale

#### Scenario: Guardrails and Fail-Safes Documented In-Line
- **WHEN** guard clauses, exception handling, or fallback pathways are added to protect downstream systems
- **THEN** inline commentary SHALL articulate the failure condition being mitigated and the intended recovery path
- **AND** the comment SHALL direct readers to monitoring or alerting artifacts where applicable
- **AND** tests SHALL assert the documented guardrail behavior to keep code and commentary aligned
