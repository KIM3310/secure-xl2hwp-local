PYTHON ?= python3
VENV ?= .venv
VENV_PYTHON := $(VENV)/bin/python
VENV_STAMP := $(VENV)/.installed-dev

.PHONY: install sample-data lint test proof verify

$(VENV_STAMP): pyproject.toml
	$(PYTHON) -m venv $(VENV)
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
