# Documentation Gate Checklist

Use this checklist in proposals and pull requests to prove documentation coverage shipped with the change. Link completed sections back to the relevant capability briefs and runbooks.

## Proposal / Spec Phase
- [ ] Identified impacted capabilities
- [ ] Listed knowledge base pages to update, including owners
- [ ] Noted new runbooks or templates required

## Implementation Phase
- [ ] Updated capability brief change log with new entry (date + change-id)
- [ ] Updated associated runbook(s) with new workflow or troubleshooting guidance
- [ ] Added/updated inline code comments for non-obvious heuristics or guardrails
- [ ] Ran `scripts/enforce_documentation.py`

## Review / Merge Phase
- [ ] Reviewer confirmed knowledge base changes render correctly
- [ ] Reviewer verified `scripts/enforce_documentation.py` passes in CI
- [ ] Governance checklist updated with documentation artifacts (links, run logs)

## Post-Merge
- [ ] Communicated updates to analysts/operators (Slack, release notes)
- [ ] Scheduled knowledge base audit if follow-up work required

