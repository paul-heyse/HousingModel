## ADDED Requirements
### Requirement: Capability Knowledge Base Maintained
The governance program SHALL maintain a living knowledge base that explains each delivered capability, why it exists, and how analysts and developers use it in practice.

#### Scenario: Capability Overview Documented
- **WHEN** a capability reaches the "Built" state in `openspec/specs`
- **THEN** the knowledge base entry SHALL describe the business objective, primary workflows, upstream dependencies, and downstream outputs for that capability
- **AND** reference canonical runbooks or notebooks that demonstrate the happy path usage
- **AND** link back to the owning spec and key code entry points for discoverability

#### Scenario: Operational Behavior Narratives Stay Current
- **WHEN** a change modifies user-facing behavior or analytical outputs
- **THEN** the corresponding knowledge base page SHALL be updated in the same change set
- **AND** the update SHALL summarize what changed, why it matters, and validation steps analysts can replay
- **AND** reviewers SHALL block merges that do not include accompanying documentation updates

### Requirement: Documentation Review Is a Governance Gate
Governance SHALL treat documentation completeness as a formal gate so spec changes, implementation work, and operational support stay synchronized.

#### Scenario: Proposal Includes Documentation Impact
- **WHEN** a new proposal is authored under `openspec/changes`
- **THEN** the proposal SHALL call out which knowledge base sections, onboarding guides, or code comments must be updated before implementation closes
- **AND** reviewers SHALL reject proposals that omit documentation impact analysis for non-trivial changes
- **AND** accepted proposals SHALL list documentation tasks alongside engineering work items

#### Scenario: Merge Checklist Blocks Incomplete Docs
- **WHEN** implementation tasks are ready for review
- **THEN** the merge checklist SHALL verify that required documentation artifacts (knowledge base pages, changelog summaries, inline code commentary) are updated or explicitly waived with justification
- **AND** pull requests lacking required documentation SHALL be considered incomplete and sent back to the author
- **AND** the checklist SHALL persist in the repository so future contributors follow the same process
