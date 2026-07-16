.PHONY: start install test check-local run-local run-sandbox

PYTHON ?= python3
# Dogfooding in the monorepo: expose starter src + monorepo package root.
MONOREPO_ROOT := $(abspath ../..)
export PYTHONPATH := src:$(CURDIR):$(MONOREPO_ROOT)$(if $(PYTHONPATH),:$(PYTHONPATH),)

# Official UX entry: print the short message to paste into any AI assistant.
start:
	$(PYTHON) scripts/start.py

install:
	@command -v poetry >/dev/null 2>&1 && poetry install || \
		$(PYTHON) -m pip install -e "$(MONOREPO_ROOT)" && \
		$(PYTHON) -m pip install -e .

test:
	$(PYTHON) -m behave tests/integration --stop --tags=@alert_connector_starter

check-local:
	$(PYTHON) scripts/check_local.py

run-local: check-local
	$(PYTHON) -m kontiki.runner.__main__ connector.service.ConnectorService \
		--config config/local.yaml

# After POST /alerts — stub
run-sandbox:
	@echo "make run-sandbox: reserved until HTTP ingestion exists"
	@exit 1
