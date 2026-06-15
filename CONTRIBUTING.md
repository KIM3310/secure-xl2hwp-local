# Contributing

## Local setup
```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -e '.[dev]'
python scripts/create_sample_excel.py
```

## Verification
Prefer the bundled commands:
```bash
make lint
make test
make proof
make verify
```

Equivalent direct commands:
```bash
ruff check app tests scripts
pytest -q
python scripts/exercise_runtime_scorecard.py
```

## Working agreements
- Preserve local-first / air-gapped runtime assumptions.
- Do not add cloud dependencies unless the requirement is explicit.
- Keep output panels (`/health`, `/ops/*`, audit exports) inspectable and stable.
- Prefer small, behavior-preserving diffs.
- Use clear conventional commits.
