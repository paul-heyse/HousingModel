# Capability: Governance Workflows

## Objective
Enforce Investment Committee (IC) gate discipline with immutable audit trails, artifact validation, and quorum tracking so deals progress only when documentation and approvals meet policy.

## Key Outcomes
- `aker_core.governance.ICWorkflow` manages gate transitions, approvals, and artifact logging against configured definitions.
- Gate definitions and quorum rules live in `governance/config.py`, enabling environment-specific policy tweaks without code edits.
- Persistent models in `governance/models.py` capture gate states, artifacts, audit events, and approval tallies tied to `run_id` metadata.
- Governance CLI (`aker_core.governance.__init__.advance`) supports scripted transitions for integration testing and batch updates.

## Architecture Snapshot
- **Entry Points**: `ICWorkflow.advance`, `ICWorkflow.submit_approval`, `ICWorkflow.check_gate_completion`.
- **Storage**: `governance_deal_gate`, `governance_gate_artifact`, `governance_ic_approval`, `governance_audit` tables managed via SQLAlchemy models.
- **Dependencies**: SQLAlchemy session, configuration loader (`get_gate_definition`, `get_ic_members`), optional CLI integration.
- **Integrations**: Links to documentation gate checklist, exports knowledge base for required artifacts, and governance dashboards in GUI.

## Operational Workflow
1. Deal owner requests gate advance via GUI/CLI with artifact references stored in object storage.
2. `ICWorkflow.advance` validates transition order and artifact completeness, then logs audit events.
3. IC members record approvals through `submit_approval` or GUI flows; quorum thresholds evaluated automatically.
4. Merge/closeout requires governance checklist sign-off plus documentation updates per this knowledge base.

## Data Lineage & Sources
| Source | Usage | Refresh Cadence | Notes |
|--------|-------|-----------------|-------|
| Governance tables | Gate state & audit trail | Real-time | Backed by Postgres; every action persisted with timestamps + user id.
| Artifact storage (S3/SharePoint) | Document attachments | Per gate change | Paths stored in `GateArtifact.reference_uri`.
| Knowledge base | Required docs & runbooks | On change | Kept in sync via documentation gate.

## Validation & QA
- `tests/test_governance.py`, `tests/test_governance_integration.py`, `tests/test_governance_performance.py` cover state machine behaviour, quorum rules, and load characteristics.
- Governance smoke flows executed via `flows/deployments.py` ensure policy remains enforced in deployment automation.
- Manual audit procedure described in governance runbook.

## Runbooks
- [Governance Workflows](../runbooks/governance-workflows.md)

## Change Log
- 2024-06-04 — Knowledge base entry created; ties governance engine to documentation gate and audit process.

