.PHONY: install test integration-test integration-test-subscription integration-test-subscription-tag integration-test-identity integration-test-identity-tag integration-test-earthquake-feed integration-test-earthquake-feed-tag integration-test-kontiki-registry-alert integration-test-kontiki-registry-alert-tag integration-test-telegram-notifier integration-test-telegram-notifier-tag cov fmt lint check clean run-service run-dev-platform run-dev-platform-no-registry down-dev-platform stack-up stack-down stack-build stack-rebuild stack-embedded-up stack-embedded-down demo-app-degrade demo-app-recover demo-app-status platform-up platform-down kontiki-tui textual-ui textual-ui-dev

PY ?= poetry run python
COMPOSE_FILE ?= docker-compose.dev.yaml
STACK_COMPOSE_FILE ?= docker-compose.stack.yaml
EMBEDDED_COMPOSE_FILE ?= docker-compose.embedded.yaml
STACK_EMBEDDED_COMPOSE = -f $(STACK_COMPOSE_FILE) -f $(EMBEDDED_COMPOSE_FILE)

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

integration-test-kontiki-registry-alert:
	poetry run behave boomerang/services/alert_services/kontiki_registry/tests/integration --stop

integration-test-kontiki-registry-alert-tag:
	poetry run behave boomerang/services/alert_services/kontiki_registry/tests/integration --stop --tags "$(TAG)"

run-dev-platform:
	docker compose -f $(COMPOSE_FILE) up -d --wait --wait-timeout 180 rabbitmq mailhog kontiki-registry

# Bus only (no kontiki-registry). Needed when Behave owns ServiceRegistry via mock
# (e.g. @fleet_state) — a real registry on the same AMQP name would race get_services.
run-dev-platform-no-registry:
	docker compose -f $(COMPOSE_FILE) stop kontiki-registry 2>/dev/null || true
	docker compose -f $(COMPOSE_FILE) rm -f kontiki-registry 2>/dev/null || true
	docker compose -f $(COMPOSE_FILE) up -d --wait --wait-timeout 180 rabbitmq mailhog

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

stack-embedded-up:
	docker compose $(STACK_EMBEDDED_COMPOSE) up -d --build --wait --wait-timeout 180

stack-embedded-down:
	docker compose $(STACK_EMBEDDED_COMPOSE) down

# Flip demo-app-service degraded flag (embedded stack must be up; MailHog: :8025).
# Heartbeat interval is 5s — wait a few seconds after degrade before checking mail.
demo-app-degrade:
	$(PY) -m boomerang.testing.demo_app.cli degrade

demo-app-recover:
	$(PY) -m boomerang.testing.demo_app.cli recover

demo-app-status:
	$(PY) -m boomerang.testing.demo_app.cli status

platform-up: stack-up

platform-down: stack-down

# -----------------------------------------------------------------------------
# Monitoring
# Prefer an already-installed kontiki-tui on PATH (pipx install / editable).
# `pipx run` alone can reuse a stale cache (e.g. 0.1.0 while PyPI is 0.1.1).
# -----------------------------------------------------------------------------
kontiki-tui:
	@if command -v kontiki-tui >/dev/null 2>&1; then \
		kontiki-tui; \
	elif command -v pipx >/dev/null 2>&1; then \
		pipx run --no-cache kontiki-tui; \
	else \
		echo "kontiki-tui not found. Install with: pipx install kontiki-tui"; \
		exit 1; \
	fi

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
