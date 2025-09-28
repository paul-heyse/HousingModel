# Aker Knowledge Base

This knowledge base complements the OpenSpec library by describing **what has been built**, **why it exists**, and **how analysts and developers operate each capability** in production. Every page is version-controlled and must be updated alongside code and spec changes.

## How It Is Organized

- `capabilities/` — One brief per deployed capability, summarizing business context, architecture, operational responsibilities, and validation steps.
- `runbooks/` — Analyst-focused procedures, troubleshooting tips, and replay steps for core workflows.
- `templates/` — Markdown scaffolds and checklists creators should copy when drafting new pages.
- `audit.md` — Rolling record of documentation coverage and identified gaps.

## Update Expectations

1. **When drafting a proposal** under `openspec/changes`, call out the knowledge base pages that require updates.
2. **During implementation**, keep the relevant capability brief and runbooks in sync with the behavior change.
3. **Reviewers** must verify documentation updates before approving merges; the governance checklist will block incomplete entries.

## Quick Navigation

| Capability | Brief | Runbook |
|------------|-------|---------|
| Core Runtime | [capabilities/core-runtime.md](capabilities/core-runtime.md) | [runbooks/core-runtime.md](runbooks/core-runtime.md) |
| ETL Connectors | [capabilities/etl-pipelines.md](capabilities/etl-pipelines.md) | [runbooks/etl-pipelines.md](runbooks/etl-pipelines.md) |
| Exports | [capabilities/exports-suite.md](capabilities/exports-suite.md) | [runbooks/exports-suite.md](runbooks/exports-suite.md) |
| Geospatial Services | [capabilities/geo-services.md](capabilities/geo-services.md) | [runbooks/geo-services.md](runbooks/geo-services.md) |
| Governance | [capabilities/governance-workflows.md](capabilities/governance-workflows.md) | [runbooks/governance-workflows.md](runbooks/governance-workflows.md) |
| GUI Dashboards | [capabilities/gui-analytics.md](capabilities/gui-analytics.md) | [runbooks/gui-analytics.md](runbooks/gui-analytics.md) |
| Jobs & Scheduling | [capabilities/jobs-orchestration.md](capabilities/jobs-orchestration.md) | [runbooks/jobs-orchestration.md](runbooks/jobs-orchestration.md) |

Start by reading the capability brief that corresponds to your area of work, then follow linked runbooks and source files for deeper context.

