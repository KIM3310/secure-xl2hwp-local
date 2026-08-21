PYTHON_MIN_VERSION := 3.10
PYTHON ?= python3
VENV ?= .venv
VENV_PYTHON := $(VENV)/bin/python
VENV_STAMP := $(VENV)/.installed-dev
PYTHON_CANDIDATES = $(VENV_PYTHON) python3.13 python3.12 python3.11 python3.10 $(PYTHON)
BOOTSTRAP_PYTHON ?= $(shell for py in $(PYTHON_CANDIDATES); do \
	if command -v $$py >/dev/null 2>&1 && $$py -c 'import sys; raise SystemExit(0 if sys.version_info >= (3, 10) else 1)' >/dev/null 2>&1; then \
		command -v $$py; \
		break; \
	fi; \
done)

.PHONY: check-bootstrap-python install sample-data lint test proof verify run

check-bootstrap-python:
	@if [ -z "$(BOOTSTRAP_PYTHON)" ]; then \
		echo "Python $(PYTHON_MIN_VERSION)+ is required." >&2; \
		echo "Install Python $(PYTHON_MIN_VERSION)+ or run: make BOOTSTRAP_PYTHON=/path/to/python$(PYTHON_MIN_VERSION) <target>" >&2; \
		exit 1; \
	fi
	@$(BOOTSTRAP_PYTHON) -c 'import sys; raise SystemExit(0 if sys.version_info >= (3, 10) else 1)' || { \
		echo "BOOTSTRAP_PYTHON=$(BOOTSTRAP_PYTHON) is not Python $(PYTHON_MIN_VERSION)+." >&2; \
		exit 1; \
	}

$(VENV_STAMP): pyproject.toml | check-bootstrap-python
	@if [ ! -x "$(VENV_PYTHON)" ] || ! $(VENV_PYTHON) -c "import sys; raise SystemExit(0 if sys.version_info >= (3, 10) else 1)" >/dev/null 2>&1; then \
		rm -rf $(VENV); \
		$(BOOTSTRAP_PYTHON) -m venv $(VENV); \
	fi
	$(VENV_PYTHON) -m pip install --upgrade pip
	$(VENV_PYTHON) -m pip install -e '.[dev]'
	@touch $(VENV_STAMP)

install: $(VENV_STAMP)

sample-data: $(VENV_STAMP)
	$(VENV_PYTHON) scripts/create_sample_excel.py

lint: $(VENV_STAMP)
	$(VENV_PYTHON) -m ruff check app tests scripts

test: $(VENV_STAMP)
	$(VENV_PYTHON) -m pytest -q

proof: $(VENV_STAMP)
	$(VENV_PYTHON) scripts/exercise_runtime_scorecard.py

verify: lint test proof

run: $(VENV_STAMP)
	$(VENV_PYTHON) -m uvicorn app.main:app --host 127.0.0.1 --port 8080
