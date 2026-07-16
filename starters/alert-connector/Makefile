.PHONY: start install test check-local run-local emit-demo run-sandbox stack-up stack-down stack-restart stack-logs

PYTHON ?= python3
COMPOSE ?= docker compose
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

# Skeleton only — requires stack-up + run-local. Replaced for real connectors.
emit-demo: check-local
	$(PYTHON) scripts/emit_demo.py

stack-up:
	$(COMPOSE) -f docker-compose.yaml up -d --build --wait --wait-timeout 180

stack-down:
	$(COMPOSE) -f docker-compose.yaml down

# Optional shortcut (down + up). After generation, prefer stack-down then stack-up when demoing.
stack-restart: stack-down stack-up

stack-logs:
	$(COMPOSE) -f docker-compose.yaml logs -f

# After POST /alerts — stub
run-sandbox:
	@echo "make run-sandbox: reserved until HTTP ingestion exists"
	@exit 1
