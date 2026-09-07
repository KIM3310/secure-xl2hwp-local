# Secure XL2HWP: design and evidence

Updated 2026-09-07.

## Design decision

Normalized spreadsheet data, template bindings and exported payloads remain separate inspectable artifacts. Distinct export names preserve prior results, while audit bundles let the reader trace an output back to its inputs.

## Inspect the code

- [app/services/export_service.py](../app/services/export_service.py): Export ownership and artifact naming.
- [tests/test_pipeline_service.py](../tests/test_pipeline_service.py): End-to-end local pipeline regression cases.

## Scope of the evidence

Cross-platform tests verify normalized files and template payloads. Native HWP generation still needs Windows and a compatible Hancom installation.

## Contribution and provenance

These notes describe what can be inspected in the repository. Commit history and pull-request diffs preserve the change trail; they do not independently establish manual versus AI-assisted authorship, team roles or contribution percentages. No such percentages are inferred here.

[Project overview](../README.md)
