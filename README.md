# Secure XL2HWP Local

**Spreadsheet cleanup and Hancom template preparation on a local machine.**

The pipeline validates and normalizes Excel data, maps it to template placeholders, and writes normalized files, a report, and a Hancom payload. Authentication and signed audit bundles support inspection of the workflow.

[Demo](https://secure-xl2hwp-local.pages.dev/) · [CI](https://github.com/KIM3310/secure-xl2hwp-local/actions/workflows/ci.yml) · [MIT](LICENSE)

## Inspect the implementation

| Engineering problem | Design decision | Code / evidence |
|---|---|---|
| Spreadsheet columns and business rules drift | Versioned contracts and cleanup profiles drive normalization. | [Excel processor](app/services/excel_processor.py) · `specs/` |
| Template fields can silently mismatch input | Build an explicit placeholder payload and report missing mappings. | [Template engine](app/services/template_engine.py) |
| Repeated runs must preserve earlier results | Every artifact set has a distinct identifier, even within one second. | [Export service](app/services/export_service.py) · [End-to-end regression](tests/test_pipeline_service.py) |

```text
Excel → contract validation → cleanup → template mapping
                                      ├─ normalized XLSX / CSV
                                      ├─ report JSON
                                      └─ Hancom payload / text preview
```

## Reproduce

Requires Python 3.10+.

```bash
make install
make verify
make sample-data
make run
```

Open `http://127.0.0.1:8080`. For login and processing, configure the users and secrets described in [the reference](REFERENCE.md#auth-setup). LLM assistance is optional; the deterministic pipeline is testable without a model provider.

## Scope

The cross-platform pipeline generates normalized files and Hancom template payloads. Creating a native HWP document requires the optional Windows connector and an installed Hancom application; the macOS checks do not validate that path. The supported topology is a single local application process. Shared deployment requires separate identity, rate limiting, persistent storage, and workstation controls.

## Further reading

- [Detailed reference](REFERENCE.md)
- [Engineering changes and regression cases](docs/engineering-notes.md)
- [Cloud architecture](docs/cloud-ai-architecture.md) · [Machine-readable blueprint](docs/architecture/blueprint.json) · [Blueprint validator](scripts/validate_architecture_blueprint.py)

[Design decisions and implementation evidence](docs/IMPLEMENTATION_NOTES.md)
