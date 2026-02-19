# Architecture

## Goal
Local-first service for secure Excel extraction and cleanup, then handoff into Hancom report workflows.

## Design Principles
- No mandatory cloud dependency
- Spec-first data contracts (SpecKit)
- CoT-style staged orchestration with deterministic fallback
- Audit-ready artifact outputs
- JWT-based API protection and actor traceability
- Air-gapped deployment support

## Pipeline
1. SpecKit Loader
2. Excel Processor (deterministic normalization + validation)
3. CoT Orchestrator (schema inference -> cleanup advice -> doc mapping)
4. Hancom Template Engine (placeholder detection + transform + table sections)
5. Export Service (normalized files + report + hancom payload + preview)
6. Optional Hancom Windows COM connector

## Runtime Security
- API endpoints are protected with JWT bearer token (except `/health`, `/auth/login`)
- User registry is loaded from `specs/security/users.yaml`
- Authentication and pipeline operations are stored in JSONL audit logs
- Request-level correlation via `X-Request-ID`

## Security Notes
- All processing can run offline on localhost
- LLM requests target local Ollama endpoint by default
- Output report contains trace and issue list for audit
- Offline bundle installer supports air-gapped runtime installation
