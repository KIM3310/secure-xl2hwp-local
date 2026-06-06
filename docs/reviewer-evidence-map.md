# Review Guide - secure-xl2hwp-local

Updated: 2026-05-30

Use this page as the short path through the repository. It keeps the review grounded in the code, docs, commands, and boundaries that are already present.

## Summary

| Field | Notes |
|---|---|
| Lane | B2B local document automation |
| Core idea | Air-gapped/local Excel-to-Hancom conversion with audit logging and signed exports. |
| Primary reader | Korean back-office, public-sector-adjacent, legal/admin, and secure internal workflow teams. |
| Stack | Python, Terraform, Docker |

## Open First

1. Start with the README fast path and architecture section.
2. Open `docs/service-launch-playbook.md` only when reviewing the product or service angle.
3. Check the commands below before making claims about quality.
4. Skim the CI workflows and fixture data before deeper implementation review.
5. Read the boundaries section before presenting the project externally.

## Checks

| Purpose | Command |
|---|---|
| Full local gate | `make verify` |
| Test suite | `make test` |

## CI

- .github/workflows/architecture-blueprint.yml
- .github/workflows/ci.yml
- .github/workflows/dependency-review.yml
- .github/workflows/pages-auto-deploy.yml
- .github/workflows/repository-health.yml
- .github/workflows/repository-surface.yml
- .github/workflows/secret-scan.yml

## Evidence

- pytest/ruff-style local verification path
- infrastructure-as-code review surface
- containerized delivery path
- make verify passes
- Sample signed export works
- Auth setup is explicit

## Commercial Notes

| Possible offer | Working scope assumption |
|---|---|
| Offline license | Scope after buyer intake |
| Controlled workflow setup | Scope after buyer intake |
| Template migration package | Scope after buyer intake |

## Boundaries

- Approved templates required
- Workstation policy needed
- Retention/signing keys customer-specific

## Useful Metrics

- Document processing time
- Template drift detection
- Signed export verification
