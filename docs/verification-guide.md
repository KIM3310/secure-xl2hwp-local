# Verification Guide

This repo is strongest when understood as a **local-first regulated automation system**, not as a public SaaS demo.

## Quick walkthrough
1. Read the positioning + trust-boundary summary in `README.md`.
2. Run `make proof` for the compact runtime snapshot.
3. Open these routes in order if you start the service locally:
   - `/health`
   - `/ops/runtime-scorecard`
   - `/ops/service-brief`
   - `/ops/readiness`
   - `/ops/architecture-pack`
4. Use `logs/audit/2026-03-15.jsonl` as the baseline evidence log showing both success and failure paths.

## What this proves
- **AI / LLM engineering signal**: spec-driven cleanup pipeline, local-model posture, deterministic fallback.
- **Solution architecture signal**: auth, path guardrails, readiness checks, signed export handoff, offline deployment.
- **Security / ops signal**: user-facing output panels are explicit instead of buried in ad hoc logs.

## Fast path commands
```bash
make test
make proof
python scripts/exercise_runtime_scorecard.py --full
```

## Evidence map
| Surface | Why it matters |
| --- | --- |
| `/health` | Bootstrap state, signing posture, and next operator action |
| `/ops/runtime-scorecard` | Compact posture summary for auth, readiness, and recent audit flow |
| `/ops/service-brief` | Trust boundary, allowed roles, architecture flow, and process contract |
| `/ops/readiness` | Preflight gate before regulated spreadsheet processing |
| `/ops/architecture-pack` | Architecture handoff surface for signed exports and approval sequence |
| `logs/audit/2026-03-15.jsonl` | Concrete audit trail with both successful and failed processing events |

## Audit baseline
The checked-in audit baseline intentionally shows both:
- a **successful** pipeline run against `examples/input/sample_projects.xlsx`
- a **failed** pipeline run against `examples/input/not_found.xlsx`

That makes the proof surface stronger because it demonstrates success-path output artifacts *and* failure-path auditability.

## What not to misread
- `site/` is a documentation surface, not the secure processing runtime.
- The strongest signal here is **deployment restraint** and **inspectable evidence**, not public-hosted inference.
- A runtime score below 100 can be expected when bootstrap is still required or when the audit sample includes a deliberate failure case.

## Framing
> I treated the product as a local secure workflow, not a cloud-first demo. The interesting part is the combination of contract-driven processing, auth/readiness gating, signed audit exports, and an air-gapped deployment story that is still inspectable.
