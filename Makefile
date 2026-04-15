.PHONY: install test integration-test integration-test-subscription cov fmt lint check clean run-service run-amqp down-amqp

PY ?= poetry run python
COMPOSE_FILE ?= docker-compose.dev.yaml

install:
	$(PY) -m pip install -U pip setuptools wheel
	poetry install || true

test:
	$(PY) -m pytest -q

integration-test: run-amqp integration-test-subscription

integration-test-subscription:
	poetry run behave boomerang/services/subscription/tests/integration --stop

run-amqp:
	docker compose -f $(COMPOSE_FILE) up -d --wait --wait-timeout 60 rabbitmq

down-amqp:
	docker compose -f $(COMPOSE_FILE) down

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

