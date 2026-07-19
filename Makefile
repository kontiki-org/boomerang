.PHONY: \
	install test cov fmt lint check clean \
	integration-test integration-test-core \
	integration-test-subscription integration-test-subscription-tag \
	integration-test-email-notifier integration-test-email-notifier-tag \
	integration-test-telegram-notifier integration-test-telegram-notifier-tag \
	integration-test-alert-engine integration-test-alert-engine-tag \
	integration-test-earthquake-feed integration-test-earthquake-feed-tag \
	run-amqp down-amqp \
	run-dev-platform run-dev-platform-no-registry down-dev-platform \
	stack-up stack-up-demo stack-down stack-build stack-rebuild \
	run-service

PY ?= poetry run python
COMPOSE_FILE ?= docker-compose.dev.yaml
STACK_COMPOSE_FILE ?= docker-compose.stack.yaml
DEMO_COMPOSE_FILE ?= docker-compose.demo.yaml
SRC = boomerang packages

install:
	$(PY) -m pip install -U pip setuptools wheel
	poetry install || true

test:
	$(PY) -m pytest -q

fmt:
	$(PY) -m isort $(SRC)
	$(PY) -m black $(SRC)

lint:
	$(PY) -m flake8 $(SRC)

check: fmt lint

cov:
	$(PY) -m pytest --cov=boomerang --cov=boomerang_contracts --cov-report=term-missing

clean:
	rm -rf .venv .mypy_cache .pytest_cache .ruff_cache .coverage dist build htmlcov

# -----------------------------------------------------------------------------
# AMQP / local deps for Behave (Kontiki-style)
# -----------------------------------------------------------------------------
run-amqp:
	docker compose -f $(COMPOSE_FILE) up -d --wait --wait-timeout 180 rabbitmq mailhog

down-amqp:
	docker compose -f $(COMPOSE_FILE) down

run-dev-platform:
	docker compose -f $(COMPOSE_FILE) up -d --wait --wait-timeout 180 rabbitmq mailhog kontiki-registry

# Bus only (no kontiki-registry). Needed when Behave owns ServiceRegistry via mock.
run-dev-platform-no-registry:
	docker compose -f $(COMPOSE_FILE) stop kontiki-registry 2>/dev/null || true
	docker compose -f $(COMPOSE_FILE) rm -f kontiki-registry 2>/dev/null || true
	docker compose -f $(COMPOSE_FILE) up -d --wait --wait-timeout 180 rabbitmq mailhog

down-dev-platform: down-amqp

# -----------------------------------------------------------------------------
# Integration tests (Behave)
# -----------------------------------------------------------------------------
# Core suites (CI). Expect RabbitMQ (:5672) + MailHog (:1025/:8025) already up.
integration-test-core:
	poetry run behave boomerang/services/subscription/tests/integration --stop
	poetry run behave boomerang/services/alert_engine/tests/integration --stop
	poetry run behave boomerang/services/notifiers/email/tests/integration --stop
	poetry run behave boomerang/services/notifiers/telegram/tests/integration --stop

integration-test: run-amqp
	@$(MAKE) integration-test-core
	@$(MAKE) integration-test-earthquake-feed

integration-test-subscription: run-amqp
	poetry run behave boomerang/services/subscription/tests/integration --stop

integration-test-subscription-tag: run-amqp
	poetry run behave boomerang/services/subscription/tests/integration --stop --tags "$(TAG)"

integration-test-email-notifier: run-amqp
	poetry run behave boomerang/services/notifiers/email/tests/integration --stop

integration-test-email-notifier-tag: run-amqp
	poetry run behave boomerang/services/notifiers/email/tests/integration --stop --tags "$(TAG)"

integration-test-telegram-notifier: run-amqp
	poetry run behave boomerang/services/notifiers/telegram/tests/integration --stop

integration-test-telegram-notifier-tag: run-amqp
	poetry run behave boomerang/services/notifiers/telegram/tests/integration --stop --tags "$(TAG)"

integration-test-alert-engine: run-amqp
	poetry run behave boomerang/services/alert_engine/tests/integration --stop

integration-test-alert-engine-tag: run-amqp
	poetry run behave boomerang/services/alert_engine/tests/integration --stop --tags "$(TAG)"

integration-test-earthquake-feed: run-amqp
	poetry run behave boomerang/services/alert_services/earthquake/tests/integration --stop

integration-test-earthquake-feed-tag: run-amqp
	poetry run behave boomerang/services/alert_services/earthquake/tests/integration --stop --tags "$(TAG)"

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

run-service:
	poetry run boomerang-subscription --config config.example.yaml
