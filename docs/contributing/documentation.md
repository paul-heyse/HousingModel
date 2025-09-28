# Documentation Gate Guidelines

All code or spec changes must ship with documentation updates that keep the knowledge base and inline commentary aligned with production behaviour. This guide explains how to work with the documentation gate introduced in `add-comprehensive-documentation`.

## Required Steps

1. **Plan**
   - During proposal authoring, identify the capabilities impacted and list the knowledge base pages that need updates.
   - Include documentation tasks in `tasks.md` and reference the `Documentation Gate Checklist` template.

2. **Implement**
   - Update capability briefs (`docs/knowledge_base/capabilities/*.md`) with a new Change Log entry referencing your change-id.
   - Update associated runbooks with new workflow steps, validation instructions, or troubleshooting notes.
   - Add or refresh docstrings and inline comments for public APIs, heuristics, and guardrails you touched.
   - Run `scripts/enforce_documentation.py` locally; fix any failures before requesting review.

3. **Review**
   - Reviewers must confirm knowledge base diffs render correctly and that docstrings/inline comments explain non-obvious logic.
   - CI will invoke `scripts/enforce_documentation.py`; treat failures as blocking issues.
   - Capture evidence (screenshots, command output) in the PR description when relevant (e.g., workbook diffs).

4. **Closeout**
   - Update governance checklist with links to the updated knowledge base pages and run logs for exports/ETL runs.
   - Communicate documentation updates to analysts or operators when behaviour changes.

## Tooling

- `scripts/enforce_documentation.py` — validates capability->runbook coverage and docstrings for critical modules.
- Knowledge base templates:
  - Capability brief: `docs/knowledge_base/templates/capability_template.md`
  - Runbook: `docs/knowledge_base/templates/runbook_template.md`
  - Documentation gate checklist: `docs/knowledge_base/templates/documentation_gate.md`

## Tips

- Keep Change Log entries short and action-oriented: `YYYY-MM-DD — change-id — summary`.
- When adding inline comments, explain *why* the logic exists, not obvious *what* it does.
- Use relative links (`../capabilities/<slug>.md`) inside runbooks to keep navigation consistent.

