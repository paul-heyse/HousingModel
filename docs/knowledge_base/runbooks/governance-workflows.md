# Runbook: Governance Gate Operations

## Purpose
Advance deals through Investment Committee gates with full artifact validation, approval tracking, and documentation compliance checks.

## Preconditions
- Governance tables migrated (`alembic upgrade head`).
- IC membership roster configured in `aker_core/governance/config.py` or environment overrides.
- Artifact storage (S3, SharePoint) accessible; required documents uploaded with stable URIs.
- Knowledge base entries updated for capability changes affecting the deal.

## Step-by-Step
1. **Review documentation checklist**
   - Confirm relevant capability briefs/runbooks reflect latest implementation.
   - Update `docs/knowledge_base` pages if gaps exist; link PR/change-id in Change Log.
2. **Prepare SQLAlchemy session**
   ```bash
   python - <<'PY'
   from sqlalchemy.orm import sessionmaker
   from aker_core.config import Settings
   from aker_data.engine import create_engine_from_url

   settings = Settings()
   engine = create_engine_from_url(settings.postgis_dsn.get_secret_value())
   Session = sessionmaker(bind=engine)
   session = Session()
   session.close()
   PY
   ```
   Replace with project-specific session factory (FastAPI/CLI usually provides one).
3. **Advance deal gate**
   ```bash
   python - <<'PY'
   from sqlalchemy.orm import sessionmaker
   from aker_core.config import Settings
   from aker_core.governance import ICWorkflow
   from aker_data.engine import create_engine_from_url

   settings = Settings()
   engine = create_engine_from_url(settings.postgis_dsn.get_secret_value())
   Session = sessionmaker(bind=engine)

   artifacts = [
       "market_analysis.pdf",
       "financial_model.xlsx",
       "governance/checklist.md",
   ]

   with Session() as session:
       workflow = ICWorkflow(session)
       gate = workflow.advance(
           deal_id=123,
           target_gate="IOI",
           artifacts=artifacts,
           user_id="analyst_jdoe",
           comment="Ready for IOI review"
       )
       print(gate.current_gate, gate.entered_at)
   PY
   ```
   Validation errors indicate missing artifacts or invalid transitions; resolve before retrying.
4. **Collect approvals**
   ```bash
   python - <<'PY'
   from sqlalchemy.orm import sessionmaker
   from aker_core.config import Settings
   from aker_core.governance import ICWorkflow
   from aker_data.engine import create_engine_from_url

   settings = Settings()
   engine = create_engine_from_url(settings.postgis_dsn.get_secret_value())
   Session = sessionmaker(bind=engine)

   with Session() as session:
       workflow = ICWorkflow(session)
       workflow.submit_approval(
           deal_id=123,
           gate="IOI",
           ic_member="ic_member_1",
           approval_type="approve",
           comment="Cleared after diligence",
       )
   PY
   ```
   Repeat until quorum reached; use `workflow.check_gate_completion(deal_id, gate)` to confirm.
5. **Audit trail export**
   ```bash
   python - <<'PY'
   from sqlalchemy.orm import sessionmaker
   from aker_core.config import Settings
   from aker_core.database.governance import GovernanceRepository
   from aker_data.engine import create_engine_from_url

   settings = Settings()
   engine = create_engine_from_url(settings.postgis_dsn.get_secret_value())
   Session = sessionmaker(bind=engine)

   with Session() as session:
       repo = GovernanceRepository(session)
       audit = repo.get_governance_audit(deal_id=123)
       for entry in audit:
           print(entry.timestamp, entry.action, entry.details)
   PY
   ```
   Store export in governance folder and link inside knowledge base change log.

## Validation
- `pytest tests/test_governance.py tests/test_governance_integration.py`.
- Verify `governance_audit` table contains entries for gate change and approvals.
- Ensure knowledge base/checklist updated before marking task complete.

## Incident Response
- **Invalid transition**: Use `workflow.get_required_artifacts(target_gate)` to list missing artifacts; confirm gate order in config.
- **Quorum not met**: Check IC roster and weights; ensure `ICApproval` votes recorded and no duplicates overwritten unexpectedly.
- **Documentation drift**: Halt progression until capability briefs/runbooks updated and reviewed.

## References
- Capability brief: [capabilities/governance-workflows.md](../capabilities/governance-workflows.md)
- Spec: `openspec/specs/governance/spec.md`
- Checklist template: [templates/documentation_gate.md](../templates/documentation_gate.md) *(created in Step 3)*

