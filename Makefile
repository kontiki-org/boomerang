.PHONY: install test integration-test integration-test-subscription integration-test-subscription-tag integration-test-identity integration-test-identity-tag cov fmt lint check clean run-service run-amqp down-amqp run-mailhog down-mailhog

PY ?= poetry run python
COMPOSE_FILE ?= docker-compose.dev.yaml

install:
	$(PY) -m pip install -U pip setuptools wheel
	poetry install || true

test:
	$(PY) -m pytest -q

integration-test: run-amqp integration-test-identity integration-test-subscription

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

integration-test-sms-notifier:
	poetry run behave boomerang/services/sms_notifier/tests/integration --stop

integration-test-sms-notifier-tag:
	poetry run behave boomerang/services/sms_notifier/tests/integration --stop --tags "$(TAG)"

integration-test-alert-engine:
	poetry run behave boomerang/services/alert_engine/tests/integration --stop

integration-test-alert-engine-tag:
	poetry run behave boomerang/services/alert_engine/tests/integration --stop --tags "$(TAG)"

run-amqp:
	docker compose -f $(COMPOSE_FILE) up -d --wait --wait-timeout 60 rabbitmq

down-amqp:
	docker compose -f $(COMPOSE_FILE) down

run-mailhog:
	docker run -d --rm --name boomerang-mailhog -p 1025:1025 -p 8025:8025 mailhog/mailhog

down-mailhog:
	docker stop boomerang-mailhog || true

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

