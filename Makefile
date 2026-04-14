.PHONY: install test cov fmt lint check clean run-service

PY ?= poetry run python

install:
	$(PY) -m pip install -U pip setuptools wheel
	poetry install || true

test:
	$(PY) -m pytest -q

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
	poetry run boomerang --config config.example.yaml

