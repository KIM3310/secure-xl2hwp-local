# Customer-Owned Secure Workflow Pilot

This is the delivery contract for the `secure-workflow-pilot` lane. It is a fixed-scope technical pilot, not a production SLA or a hosted document service.

## Outcome

Adapt and verify one approved Excel-to-Hancom workflow inside a customer-owned environment. Success is measured with a baseline and target such as operator minutes per document, template-drift catches, correction rate, or signed-handoff verification rate.

## Included

1. Workflow and template boundary workshop.
2. Synthetic-data walkthrough before customer files.
3. One contract/profile/template mapping.
4. Customer-owned single-process installation profile.
5. Secret generation and rotation checklist.
6. Upstream rate-limit and persistent audit-storage acceptance checks.
7. Signed export verification evidence.
8. Operator runbook and production gap report.

## Required Customer Controls

- Customer-generated runtime and signing secrets.
- Customer identity or approved gateway policy for shared access.
- Upstream TLS, request limits, and rate limiting.
- Persistent audit/output storage with backup, retention, and recovery owners.
- Approved template rights, workstation policy, rollback owner, and support contact.

## Explicit Exclusions

- Multi-worker or horizontally scaled application runtime.
- Bundled SSO/OIDC, WAF, shared rate-limit store, or centralized audit database.
- Vendor-hosted documents, audit logs, or customer credentials.
- Compliance certification, legal assurance, unattended production rollout, or production SLA.

## Acceptance Evidence

- `make verify` passes on the delivered revision.
- `/health` reports the customer-owned pilot boundary and `production_ready=false`.
- `/ops/readiness` has no failed checks for the approved pilot profile.
- The customer demonstrates upstream throttling and storage persistence.
- A representative output and signed audit bundle pass independent verification.

Start a private scoping request through the [Secure Workflow Pilot intake](https://kim3310-doeon-kim-portfolio.pages.dev/?offer=secure-xl2hwp-local&inquiry=secure-workflow-pilot#private-inquiry). Do not include credentials or customer documents in the inquiry.
