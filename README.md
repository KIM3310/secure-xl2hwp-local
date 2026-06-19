# secure-xl2hwp-local

Excel-to-Hancom document conversion platform designed for air-gapped and local secure environments. Cleans spreadsheet data using contract-based rules and maps it to Hancom (HWP) templates, with full audit logging and signed exports.

Architecture pack: [`docs/architecture-pack.md`](docs/architecture-pack.md)

## Product and System Surface

A local-first Korean document automation tool that turns repetitive Excel-to-Hancom work into signed, auditable exports.

| Lens | Definition |
|---|---|
| Audience | Korean back-office teams, public-sector-adjacent operators, legal/admin teams, and secure internal workflow owners. |
| Architecture path | Validate the demo, README, architecture notes, and quality gate before deeper workflow architecture. |
| System signal | JWT auth, signed exports, audit logs, local operation, structured output, and Hancom-focused workflow design. |
| Safety boundary | Designed for controlled local use; real deployments need approved templates, retention rules, and workstation policies. |
| Fast path | Run the backend checks and generate a sample signed export from staged input data. |

## System Fast Path

- **First minute:** Check the auth setup, template drift preview, signed export, and audit timeline.
- **Local demo:** Run `make install`, `make sample-data`, and `uvicorn app.main:app --host 127.0.0.1 --port 8080`; open `http://127.0.0.1:8080/`.
- **Verification:** Run `make verify`; it covers lint, tests, and signed proof generation.

## Service Launch Playbook

- [Service launch playbook](docs/service-launch-playbook.md) maps the repository to architecture audiences, operating gates, operating boundaries, and risk controls.

## Architecture Notes

- [Architecture guide](docs/architecture-evidence-map.md) summarizes the project angle, first files to inspect, runtime commands, and known boundaries.
- [Quality notes](docs/quality-gate.md) lists the local checks, CI surface, and release expectations for this repository.
- [Enterprise readiness notes](docs/enterprise-readiness.md) outlines security, data, operations, integration, and handoff expectations.

## Key Features

- **SpecKit**: Contract/profile/template specs that control the pipeline
- **CoT pipeline**: Schema inference -> cleanup advice -> document mapping
- **Hancom templates**: Placeholder detection + transform rules + auto table generation
- **Template drift preview**: Shows placeholder/spec mismatches before export
- **JWT auth**: `/auth/login`, `/auth/me`, protected processing APIs
- **Audit log**: Login/processing events recorded as `jsonl`
- **Offline deployment**: Wheel bundles and air-gapped install scripts
- **Signed exports**: HMAC-SHA256 signed audit bundles with verification

## Quickstart

```bash
cd secure-xl2hwp-local
python3 -m venv .venv
source .venv/bin/activate
pip install '.[dev]'
cp .env.example .env
python scripts/create_sample_excel.py
```

Or use Make:
```bash
make install
make sample-data
```

### Optional: Ollama models
```bash
ollama pull qwen2.5:7b
ollama pull qwen2.5:14b
```

Set `ENABLE_LLM=false` in `.env` if not using Ollama. The deterministic pipeline still runs when the LLM is unavailable.

## Running

```bash
uvicorn app.main:app --host 127.0.0.1 --port 8080
```

Web UI at `http://127.0.0.1:8080/`

Features: login/JWT session, path/file mode execution, metrics visualization, audit timeline, bilingual UI (Korean/English), theme toggle, signed export + verification.

## Auth Setup

The default `specs/security/users.yaml` is empty. Before using:

1. Set strong values for `JWT_SECRET_KEY`, `AUTH_PASSWORD_PEPPER`, `EXPORT_SIGNING_KEY` in `.env`
2. Generate password hashes: `python scripts/hash_password.py --password 'StrongPassword!' --pepper 'YOUR_PEPPER'`
3. Write `specs/security/users.yaml` with the hash
4. Configure `PROCESS_ALLOWED_ROLES` and path restrictions

## API Endpoints

| Endpoint | Description |
|---|---|
| `POST /auth/login` | JWT login |
| `GET /auth/me` | Current user info |
| `POST /process/path` | Process spreadsheet by path |
| `GET /health` | Bootstrap state, signing status |
| `GET /ops/readiness` | Pre-flight checks |
| `GET /ops/service-brief` | Allowed roles, trust boundary |
| `GET /ops/runtime-scorecard` | Runtime health summary |
| `GET /ops/architecture-pack` | Export evidence and approval gates |
| `GET /ops/audit/recent` | Recent audit events |
| `GET /ops/audit/export/summary.bundle.zip` | Signed audit bundle |
| `POST /ops/audit/export/verify` | Verify export signatures |

## Output Artifacts

- `*.normalized.*.xlsx` / `*.normalized.*.csv`
- `*.report.*.json`
- `*.hancom_payload.*.json`
- `*.hancom_preview.*.txt`

## Project Structure

```text
app/
  api/                 # API schemas
  connectors/          # Optional Hancom Windows COM connector
  core/                # Settings, logging
  pipeline/            # CoT orchestrator
  services/            # Auth/Audit/SpecKit/Template/Export/Pipeline
specs/
  contracts/           # Data contract YAML
  profiles/            # Cleanup profile YAML
  templates/           # Hancom template mapping
  security/            # Local users registry
scripts/
examples/
docs/
```

## Tests

```bash
pytest -q
ruff check app tests scripts
```

97 tests covering JWT auth, login guard thread safety, export signature verification, CoT pipeline stages, and path traversal blocking.

## Docs

- Usage guide (KO): `docs/usage-ko.md`
- User guide (EN): `docs/usage-en.md`
- Architecture: `docs/architecture.md`
- SpecKit: `docs/speckit.md`
- CoT design: `docs/cot.md`
- Offline deploy: `docs/offline-deploy.md`

## License

MIT

## Cloud + AI Architecture

This repository includes a neutral cloud and AI engineering blueprint that maps the current proof surface to runtime boundaries, data contracts, model-risk controls, deployment posture, and validation hooks.

- [Cloud + AI architecture blueprint](docs/cloud-ai-architecture.md)
- [Machine-readable architecture manifest](docs/architecture/blueprint.json)
- Validation command: `python3 scripts/validate_architecture_blueprint.py`

## Enterprise Productization

- [Product operating model](docs/product-operating-model.md) defines the architecture inspection, trust boundary, trust boundary, operating checks, and service path for this repository.

## System Architecture

- [System architecture](docs/system-architecture.md) maps the runtime boundary, data/control flow, cloud or local deployment surface, and operating assumptions for this repository.

## Service Architecture

- [Service architecture](docs/service-architecture.md) defines the cloud resources, account information, cost controls, and production guardrails needed to turn this repo into a scoped service without publishing public financial assumptions.

<!-- search-growth-readme:start -->

## Search And Service Surface

- Public entry: public architecture page that explains trust boundary and handoff path
- Paid boundary: paid local license, deployment package, and template adaptation support
- Canonical URL: https://secure-xl2hwp-local.pages.dev/
- Lead capture: mailto:ehdjs1351@gmail.com?subject=Secure%20XL2HWP%20Local%20private%20workspace&body=I%20am%20interested%20in%20paid%20local%20license%2C%20deployment%20package%2C%20and%20template%20adaptation%20support%20for%20Secure%20XL2HWP%20Local.
- Machine-readable offer: [docs/service-offer.json](docs/service-offer.json)
- Search growth implementation: [docs/search-growth-implementation.md](docs/search-growth-implementation.md)
- Revenue architecture: [docs/revenue-architecture.md](docs/revenue-architecture.md)

<!-- search-growth-readme:end -->
