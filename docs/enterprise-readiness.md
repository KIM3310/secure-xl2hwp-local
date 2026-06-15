# Enterprise Readiness Notes - secure-xl2hwp-local

Updated: 2026-05-30

This note defines what an enterprise technical reader, public-sector operator, serious user, or technical evaluator can safely infer from this repository today. It is intentionally conservative: public proof is separated from production claims.

## Scope

| Field | Notes |
|---|---|
| Repository | `secure-xl2hwp-local` |
| Lane | B2B local document automation |
| Primary reader | Korean back-office, public-sector-adjacent, legal/admin, and secure internal workflow teams. |
| Core wedge | Air-gapped/local Excel-to-Hancom conversion with audit logging and signed exports. |
| Stack | Python, Terraform, Docker |
| Readiness posture | Pilot-ready technical surface; production use requires customer-specific identity, monitoring, data, and support controls. |

## Enterprise Controls

| Control | Current expectation |
|---|---|
| Data boundary | Customer documents require approved storage, document-rights checks, redaction policy, and inspectable retrieval/evaluation logs. |
| Identity and access | Production pilots should add SSO/OIDC, RBAC, scoped service accounts, secret rotation, and admin-visible access architectures. |
| Auditability | Keep decision logs, generated reports, CI results, eval outputs, and operator handoff artifacts inspectable. |
| Observability | Track health checks, latency, error budget, cost, eval pass rate, audit-log completeness, and handoff/report generation status. |
| Release gate | Full local gate: make verify; Test suite: make test |
| Support handoff | Name the owner, escalation path, rollback path, known limits, and architecture cadence before a production testing. |

## Verification Surface

| Purpose | Command |
|---|---|
| Full local gate | `make verify` |
| Test suite | `make test` |

## CI Surface

- .github/workflows/architecture-blueprint.yml
- .github/workflows/ci.yml
- .github/workflows/dependency-architecture.yml
- .github/workflows/pages-auto-deploy.yml
- .github/workflows/repository-health.yml
- .github/workflows/repository-surface.yml
- .github/workflows/secret-scan.yml

## Acceptance Criteria

- make verify can be run or the equivalent CI gate is visible.
- README, architecture guide, quality notes, service model, and this readiness note agree on the same scope.
- Demo, fixture, synthetic, or public-data boundaries are explicit before a technical reader sees outputs.
- A technical reader can identify the first useful outcome without reading implementation details.
- Production claims stay behind customer-specific validation, access control, monitoring, and support handoff.

## Integration Path

- Run a synthetic-data walkthrough with the technical reader and document the acceptance criteria.
- Scope a controlled pilot using approved data, named users, secrets, and rollback paths.
- Convert the pilot into an operating handoff with monitoring, architecture cadence, support owner, and renewal metric.

## Proof Points

- make verify passes
- Sample signed export works
- Auth setup is explicit

## Operating Metrics

- Document processing time
- Template drift detection
- Signed export verification

## Open Risks

- Approved templates required
- Workstation policy needed
- Retention/signing keys customer-specific

## Finish Line

- Keep the public repository honest, runnable, and easy to architecture.
- Keep sensitive data, secrets, private tenant details, and unsupported claims out of public artifacts.
- Treat this repository as a proof surface until an approved pilot defines users, data, access, monitoring, support, and success metrics.
