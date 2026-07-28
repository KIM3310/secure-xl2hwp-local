# Product Operating Model

Repository: `secure-xl2hwp-local`
Last updated: 2026-06-03 KST

## Enterprise Product Position

Local-first secure Excel extraction/cleanup to Hancom payload workflow with SpecKit + CoT pipeline

This repository is packaged as a concrete system surface, not a loose code sample. The enterprise value is a narrow proof that can be inspected, run, tested, and converted into a scoped implementation motion.

## Audience And Service Path

| Area | Position |
| --- | --- |
| Target users | Korean back-office teams with local document workflows |
| Service wedge | Fixed-scope customer-owned secure workflow pilot |
| System signal | Local-first security, signed exports, auditability |
| Delivery shape | One approved workflow, single-process customer runtime, explicit perimeter and storage gates, signed handoff evidence, and an operator runbook |
| Expansion path | Add customer-specific adapters, policy controls, observability, and support SLAs after the pilot proves value |

## Enterprise Trust Boundary

- Keep credentials out of the repository and require environment-based configuration for live integrations.
- Keep customer files, runtime secrets, audit logs, and generated documents inside the customer's runtime and accounts.
- Treat the built-in login guard and audit hash chain as process-local controls. They do not support multi-worker or horizontally scaled deployment.
- Require upstream throttling, customer identity controls, persistent audit storage, and named backup/retention owners before shared access.
- Treat generated screenshots, fixtures, and sample data as non-customer proof assets unless explicitly approved.
- Keep CI, repository-surface validation, architecture manifest checks, and secret scanning green before presenting the repo externally.
- Use the architecture blueprint as the source of truth for cloud, AI, data, and operational boundaries.
- Document any unsupported production assumption before a customer or evaluator sees the demo.

## Operating Model

| Function | Standard |
| --- | --- |
| Local verification | `make verify` |
| Runtime stack | Python, Makefile automation |
| Demo readiness | README, architecture docs, and proof assets should explain the first five minutes of evaluation. |
| Support handoff | Capture setup, known limits, recovery steps, and customer-specific extension points before a production test. |
| Release discipline | Do not ship dependency mega-bumps, workflow edits, or demo URL changes without rerunning repository validators and project checks. |

## Debug And Reliability Checklist

1. Start with the README quickstart and the local verification command above.
2. Confirm `.github/workflows` checks match the local command path.
3. Confirm architecture and repository-surface validators pass after docs, workflow, or positioning changes.
4. Inspect public demos and homepage metadata before linking the repo from the project index.
5. Record any failing external dependency as an explicit operating limitation instead of hiding it.

## Service Next Step

Route qualified demand to the `secure-workflow-pilot` lane. The paid scope is one approved Excel-to-Hancom workflow with measurable time/error reduction, customer-owned deployment, signed handoff verification, and an explicit production gap report.
