CLIENT ?= partacademy

VENV   := .venv
PY     := $(VENV)/bin/python
PIP    := $(VENV)/bin/pip

.PHONY: venv install help clients show validate reports test

venv:
	python3 -m venv $(VENV)

install: venv
	$(PIP) install -U pip
	$(PIP) install -r requirements.txt

help: install
	$(PY) -m app.cli --help

clients: install
	$(PY) -m app.cli clients

show: install
	$(PY) -m app.cli show $(CLIENT)

validate: install
	$(PY) -m app.cli validate $(CLIENT)

# Generate reports for a client (requires P1_START, P1_END, P2_START, P2_END)
# Example: make reports CLIENT=partacademy P1_START=2024-12-01 P1_END=2024-12-31 P2_START=2025-12-01 P2_END=2025-12-31
reports: install
	@if [ -z "$(P1_START)" ] || [ -z "$(P1_END)" ] || [ -z "$(P2_START)" ] || [ -z "$(P2_END)" ]; then \
		echo "Error: P1_START, P1_END, P2_START, P2_END must be set"; \
		echo "Example: make reports CLIENT=partacademy P1_START=2024-12-01 P1_END=2024-12-31 P2_START=2025-12-01 P2_END=2025-12-31"; \
		exit 1; \
	fi
	$(PY) -m app.cli analyze-sources $(CLIENT) $(P1_START) $(P1_END) $(P2_START) $(P2_END) --refresh
	$(PY) -m app.cli analyze-pages $(CLIENT) $(P1_START) $(P1_END) $(P2_START) $(P2_END) --refresh
	@echo "Reports generated in data_cache/$(CLIENT)/"

test: install
	$(PIP) install pytest pytest-mock
	$(PY) -m pytest tests/ -v
