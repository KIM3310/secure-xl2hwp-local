# Secure XL2HWP Local - Usage Guide (EN)

This guide explains how to run and use the service in a local or air-gapped environment.

## 1. What This Service Does
- Transforms Excel data into structured outputs and Hancom-ready payloads.
- Uses spec-driven rules (`contracts`, `profiles`, `templates`) for repeatable processing.
- Supports security controls: JWT auth, role checks, audit logs, signed exports, path restrictions.

## 2. Prerequisites
- Python `3.10+`
- macOS/Linux shell (examples use `zsh/bash`)
- Optional: Ollama (only if you want local LLM features)

## 3. Install
```bash
cd secure-xl2hwp-local
python3 -m venv .venv
source .venv/bin/activate
pip install '.[dev]'
cp .env.example .env
python scripts/create_sample_excel.py
```

## 4. Configure Security Secrets
Edit `.env` and set strong values:
- `JWT_SECRET_KEY`
- `AUTH_PASSWORD_PEPPER`
- `EXPORT_SIGNING_KEY`

Also review policy settings:
- `PROCESS_ALLOWED_ROLES`
- `AUTH_LOGIN_MAX_FAILURES`, `AUTH_LOGIN_WINDOW_SECONDS`, `AUTH_LOGIN_LOCK_SECONDS`
- `ALLOWED_INPUT_BASE_DIR`, `ALLOWED_OUTPUT_BASE_DIR`, `ALLOWED_TEMPLATE_BASE_DIR`

## 5. Create Your First Admin Account
The repository ships with an empty `specs/security/users.yaml` by design.

Generate password hash:
```bash
python scripts/hash_password.py \
  --password 'StrongPassword!' \
  --pepper 'YOUR_AUTH_PASSWORD_PEPPER'
```

Register the user in `specs/security/users.yaml`:
```yaml
users:
  - user_id: "local-admin"
    role: "Admin"
    password_hash: "PASTE_HASH_HERE"
    active: true
```

Available roles:
- `Admin`: process + audit + exports
- `Auditor`: audit + exports
- `Analyst`: process only (if allowed by `PROCESS_ALLOWED_ROLES`)

## 6. Run the Service
```bash
uvicorn app.main:app --host 127.0.0.1 --port 8080
```

Open UI:
- `http://127.0.0.1:8080/`

## 7. Use the UI (Typical Flow)
1. Login with your admin account.
2. Choose `Path Mode` or `File Mode`.
3. Run the pipeline.
4. Review metrics, artifacts, and response JSON.
5. Check audit/ops panels.
6. Export signed bundles and verify signatures.

If this is the first run, the login panel shows an admin onboarding card with Korean/English toggle and setup steps.

## 8. API Quick Test
Login:
```bash
curl -sS -X POST http://127.0.0.1:8080/auth/login \
  -H 'Content-Type: application/json' \
  -d '{"user_id":"local-admin","password":"StrongPassword!"}'
```

Process by path:
```bash
TOKEN="<access_token>"
curl -sS -X POST http://127.0.0.1:8080/process/path \
  -H "Authorization: Bearer $TOKEN" \
  -H 'Content-Type: application/json' \
  -d '{
    "input_path":"examples/input/sample_projects.xlsx",
    "output_dir":"examples/output",
    "contract_name":"default",
    "profile_name":"default",
    "template_name":"default",
    "template_path":"examples/input/sample_report_template.txt"
  }'
```

## 9. Optional Ollama Setup
```bash
ollama pull qwen2.5:7b
ollama pull qwen2.5:14b
```

If Ollama is not available, set `ENABLE_LLM=false` in `.env`.

## 10. Troubleshooting
- `401 Invalid credentials`
  - Verify `users.yaml` contains an active user and hash was generated with the same `AUTH_PASSWORD_PEPPER`.
- `429 Too many failed login attempts`
  - Wait for lock time (`AUTH_LOGIN_LOCK_SECONDS`) or adjust policy.
- `400 ... must stay under configured base directory`
  - Your `input_path`, `output_dir`, or `template_path` is outside allowed base directories.
- `403 Insufficient role`
  - The user role is not allowed for that endpoint.
- `413 exceeds max size limit`
  - Increase `MAX_UPLOAD_MB` or reduce file size.

## 11. Related Docs
- Architecture: `docs/architecture.md`
- SpecKit details: `docs/speckit.md`
- CoT pipeline: `docs/cot.md`
- Offline deploy: `docs/offline-deploy.md`
