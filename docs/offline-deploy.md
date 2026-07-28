# Offline Deployment (Air-gapped)

## 1) Build bundle on connected machine
```bash
cd secure-xl2hwp-local
bash scripts/build_offline_bundle.sh
```

Output:
- `dist/secure-xl2hwp-offline-bundle.tar.gz`

## 2) Move tarball to air-gapped machine
USB, internal mirror, or approved transfer channel.

## 3) Install offline on air-gapped machine
```bash
mkdir -p /opt/secure-xl2hwp
cd /opt/secure-xl2hwp
tar -xzf secure-xl2hwp-offline-bundle.tar.gz
bash install_offline.sh /opt/secure-xl2hwp/runtime
```

## 4) Configure
```bash
cd /opt/secure-xl2hwp/runtime
cp .env.example .env
# Generate independent organization-owned values for:
# JWT_SECRET_KEY, AUTH_PASSWORD_PEPPER, EXPORT_SIGNING_KEY
#
# Then set:
# APP_ENV=pilot
# RUNTIME_OWNER=customer
# RUNTIME_WORKERS=1
# AUTH_RATE_LIMIT_MODE=upstream-enforced
# AUDIT_STORAGE_MODE=persistent-filesystem
```

Do not reuse secrets from a demo or another environment. The customer owns creation, storage, rotation, recovery, and revocation.

## 5) Prepare Persistent State

- Put `logs/audit`, input, output, and template paths on customer-approved storage.
- Define backup, restore, retention, deletion, and access-review owners.
- Verify that the runtime account cannot escape the configured base directories.
- Keep one application process. The login guard and audit hash chain are not cross-process safe.

## 6) Put Shared Access Behind A Customer Perimeter

The application does not provision an upstream control. Before binding beyond loopback, configure a customer-operated reverse proxy or gateway with TLS, identity policy, request-size limits, and rate limiting. Setting `AUTH_RATE_LIMIT_MODE=upstream-enforced` records that operating contract; it does not prove the gateway exists.

## 7) Run
```bash
source .venv/bin/activate
uvicorn app.main:app --host 127.0.0.1 --port 8080
```

Do not add `--workers` greater than `1`.

## 8) Acceptance

1. Open `/health` and confirm `runtime_boundary.pilot_ready=true`.
2. Confirm `runtime_boundary.production_ready=false`; this is expected and prevents overclaiming.
3. Run `/ops/readiness` as an admin and resolve failed checks.
4. Verify upstream throttling independently.
5. Generate and verify a signed export bundle.
6. Test backup and restore of audit and output directories before approved data is used.
