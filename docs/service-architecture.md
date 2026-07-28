# Service Architecture - secure-xl2hwp-local

This document defines the supported customer-owned pilot boundary. It does not describe a vendor-hosted SaaS or claim production readiness.

## Runtime Boundary

```text
Public proof site (no customer data)
  -> private scoping intake (no credentials or documents)
  -> customer gateway / reverse proxy
       - TLS
       - customer identity policy
       - request and rate limits
  -> one secure-xl2hwp-local process
       - configured input/template/output base directories
       - process-local login guard
       - process-local audit append/hash state
  -> customer persistent filesystem
       - audit JSONL
       - normalized documents
       - signed export bundles
```

## Ownership

| Resource | Owner | Repository responsibility |
|---|---|---|
| Public site | Vendor | Static documentation only |
| Runtime host and network | Customer | Installation profile and validation checklist |
| Identity and upstream rate limit | Customer | Required contract; not provisioned by this repo |
| Runtime/signing secrets | Customer | Fail-closed validation; no secret custody |
| Input, templates, outputs, audit logs | Customer | Path guards, signed bundles, and local verification |
| Backup, retention, recovery, monitoring | Customer | Acceptance evidence and production-gap handoff |

## Supported Topology

- Exactly one application process.
- Multiple threads inside that process are serialized where the local guard and audit writer require it.
- Multiple workers, replicas, or horizontally scaled hosts are unsupported because login attempts and the audit hash chain do not share state.
- Shared access must stay behind an independently verified customer perimeter.

## Protected Runtime Gate

`APP_ENV=pilot`, `staging`, or `prod` fails at settings validation unless:

- `RUNTIME_OWNER=customer`
- `RUNTIME_WORKERS=1`
- `AUTH_RATE_LIMIT_MODE=upstream-enforced`
- `AUDIT_STORAGE_MODE=persistent-filesystem`
- auth and export signing are enabled
- JWT, password-pepper, and signing secrets are explicit and non-placeholder

These values assert an operating contract. They do not detect or provision the upstream gateway, persistent mount, backup, or identity system; the pilot acceptance procedure verifies those controls separately.

## Promotion Beyond Pilot

Production promotion requires a separate design and implementation for customer identity, shared login-throttle state, atomic centralized audit storage, high availability, backup/restore automation, observability, vulnerability management, incident ownership, and SLA. Until those controls exist and are validated, runtime payloads intentionally report `production_ready=false`.
