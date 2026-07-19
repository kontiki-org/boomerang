.PHONY: install test integration-test integration-test-subscription integration-test-subscription-tag integration-test-email-notifier integration-test-email-notifier-tag integration-test-telegram-notifier integration-test-telegram-notifier-tag integration-test-alert-engine integration-test-alert-engine-tag integration-test-earthquake-feed integration-test-earthquake-feed-tag cov fmt lint check clean run-service run-dev-platform run-dev-platform-no-registry down-dev-platform stack-up stack-up-demo stack-down stack-build stack-rebuild

PY ?= poetry run python
COMPOSE_FILE ?= docker-compose.dev.yaml
STACK_COMPOSE_FILE ?= docker-compose.stack.yaml
DEMO_COMPOSE_FILE ?= docker-compose.demo.yaml

install:
	$(PY) -m pip install -U pip setuptools wheel
	poetry install || true

test:
	$(PY) -m pytest -q

integration-test: integration-test-subscription integration-test-email-notifier integration-test-telegram-notifier integration-test-alert-engine integration-test-earthquake-feed

integration-test-subscription:
	poetry run behave boomerang/services/subscription/tests/integration --stop

integration-test-subscription-tag:
	poetry run behave boomerang/services/subscription/tests/integration --stop --tags "$(TAG)"

integration-test-email-notifier:
	poetry run behave boomerang/services/email_notifier/tests/integration --stop

integration-test-email-notifier-tag:
	poetry run behave boomerang/services/email_notifier/tests/integration --stop --tags "$(TAG)"

integration-test-telegram-notifier:
	poetry run behave boomerang/services/telegram_notifier/tests/integration --stop

integration-test-telegram-notifier-tag:
	poetry run behave boomerang/services/telegram_notifier/tests/integration --stop --tags "$(TAG)"

integration-test-alert-engine:
	poetry run behave boomerang/services/alert_engine/tests/integration --stop

integration-test-alert-engine-tag:
	poetry run behave boomerang/services/alert_engine/tests/integration --stop --tags "$(TAG)"

integration-test-earthquake-feed:
	poetry run behave boomerang/services/alert_services/earthquake/tests/integration --stop

integration-test-earthquake-feed-tag:
	poetry run behave boomerang/services/alert_services/earthquake/tests/integration --stop --tags "$(TAG)"

run-dev-platform:
	docker compose -f $(COMPOSE_FILE) up -d --wait --wait-timeout 180 rabbitmq mailhog kontiki-registry

# Bus only (no kontiki-registry). Needed when Behave owns ServiceRegistry via mock
# (e.g. registry race with get_services in integration tests).
run-dev-platform-no-registry:
	docker compose -f $(COMPOSE_FILE) stop kontiki-registry 2>/dev/null || true
	docker compose -f $(COMPOSE_FILE) rm -f kontiki-registry 2>/dev/null || true
	docker compose -f $(COMPOSE_FILE) up -d --wait --wait-timeout 180 rabbitmq mailhog

down-dev-platform:
	docker compose -f $(COMPOSE_FILE) down

# -----------------------------------------------------------------------------
# Local stack (core alerting runtime)
# -----------------------------------------------------------------------------
stack-build:
	docker compose -f $(STACK_COMPOSE_FILE) build

stack-rebuild:
	docker compose -f $(STACK_COMPOSE_FILE) build --no-cache

stack-up:
	docker compose -f $(STACK_COMPOSE_FILE) up -d --build --wait --wait-timeout 180

stack-up-demo:
	docker compose -f $(STACK_COMPOSE_FILE) -f $(DEMO_COMPOSE_FILE) up -d --build --wait --wait-timeout 180

stack-down:
	docker compose -f $(STACK_COMPOSE_FILE) -f $(DEMO_COMPOSE_FILE) down

cov:
	$(PY) -m pytest --cov=. --cov-report=term-missing

fmt:
	$(PY) -m isort .
	$(PY) -m black .

lint:
	$(PY) -m flake8 .

check: fmt lint

clean:
	rm -rf .venv .mypy_cache .pytest_cache .ruff_cache .coverage dist build

run-service:
	poetry run boomerang-subscription --config config.example.yaml
