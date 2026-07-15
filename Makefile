.PHONY: install test integration-test integration-test-subscription integration-test-subscription-tag integration-test-identity integration-test-identity-tag integration-test-earthquake-feed integration-test-earthquake-feed-tag integration-test-telegram-notifier integration-test-telegram-notifier-tag cov fmt lint check clean run-service run-dev-platform down-dev-platform stack-up stack-down stack-build stack-rebuild platform-up platform-down kontiki-tui textual-ui textual-ui-dev

PY ?= poetry run python
COMPOSE_FILE ?= docker-compose.dev.yaml
STACK_COMPOSE_FILE ?= docker-compose.stack.yaml

install:
	$(PY) -m pip install -U pip setuptools wheel
	poetry install || true

test:
	$(PY) -m pytest -q

integration-test: integration-test-identity integration-test-subscription

integration-test-subscription:
	poetry run behave boomerang/services/subscription/tests/integration --stop

integration-test-subscription-tag:
	poetry run behave boomerang/services/subscription/tests/integration --stop --tags "$(TAG)"

integration-test-identity:
	poetry run behave boomerang/services/identity/tests/integration --stop

integration-test-identity-tag:
	poetry run behave boomerang/services/identity/tests/integration --stop --tags "$(TAG)"

integration-test-email-notifier:
	poetry run behave boomerang/services/email_notifier/tests/integration --stop

integration-test-email-notifier-tag:
	poetry run behave boomerang/services/email_notifier/tests/integration --stop --tags "$(TAG)"

integration-test-telegram-notifier:
	poetry run behave boomerang/services/telegram_notifier/tests/integration --stop

integration-test-telegram-notifier-tag:
	poetry run behave boomerang/services/telegram_notifier/tests/integration --stop --tags "$(TAG)"

integration-test-sms-notifier:
	poetry run behave boomerang/services/sms_notifier/tests/integration --stop

integration-test-sms-notifier-tag:
	poetry run behave boomerang/services/sms_notifier/tests/integration --stop --tags "$(TAG)"

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

down-dev-platform:
	docker compose -f $(COMPOSE_FILE) down

# -----------------------------------------------------------------------------
# Local stack (RabbitMQ + optional Mailhog)
# -----------------------------------------------------------------------------
stack-build:
	docker compose -f $(STACK_COMPOSE_FILE) build

stack-rebuild:
	docker compose -f $(STACK_COMPOSE_FILE) build --no-cache

stack-up:
	docker compose -f $(STACK_COMPOSE_FILE) up -d --build --wait --wait-timeout 180

stack-down:
	docker compose -f $(STACK_COMPOSE_FILE) down

platform-up: stack-up

platform-down: stack-down

# -----------------------------------------------------------------------------
# Monitoring (PyPI)
# -----------------------------------------------------------------------------
kontiki-tui:
	@command -v pipx >/dev/null 2>&1 || ( \
		echo "pipx is required to run kontiki-tui without using a local repo."; \
		echo "Install pipx then run: pipx run kontiki-tui"; \
		exit 1; \
	)
	pipx run kontiki-tui

textual-ui:
	$(PY) -m pip install -e ./apps/textual
	$(PY) -m boomerang_textual.app

textual-ui-dev:
	$(PY) -m boomerang_textual.app

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
