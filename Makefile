CLIENT ?= partacademy

VENV   := .venv
PY     := $(VENV)/bin/python
PIP    := $(VENV)/bin/pip

.PHONY: venv install help clients show validate

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
