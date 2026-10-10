.PHONY: \
	install fmt lint check clean \
	integration-test integration-test-core \
	integration-test-subscription integration-test-subscription-tag \
	integration-test-email-notifier integration-test-email-notifier-tag \
	integration-test-telegram-notifier integration-test-telegram-notifier-tag \
	integration-test-ntfy-notifier integration-test-ntfy-notifier-tag \
	integration-test-alert-engine integration-test-alert-engine-tag \
	integration-test-earthquake-feed integration-test-earthquake-feed-tag \
	run-dev-platform down-dev-platform \
	stack-up stack-up-demo stack-down stack-build stack-rebuild \
	run-service \
	publish-subscription publish-alert-engine \
	publish-email-notifier publish-telegram-notifier publish-ntfy-notifier

PY ?= poetry run python
COMPOSE_FILE ?= docker-compose.dev.yaml
STACK_COMPOSE_FILE ?= docker-compose.stack.yaml
DEMO_COMPOSE_FILE ?= docker-compose.demo.yaml
SRC = boomerang packages

install:
	$(PY) -m pip install -U pip setuptools wheel
	poetry install || true

fmt:
	$(PY) -m isort $(SRC)
	$(PY) -m black $(SRC)

lint:
	$(PY) -m flake8 $(SRC)

check: fmt lint

clean:
	rm -rf .venv .mypy_cache .pytest_cache .ruff_cache .coverage dist build htmlcov

# -----------------------------------------------------------------------------
# Local deps for Behave (RabbitMQ + MailHog + kontiki-registry)
# -----------------------------------------------------------------------------
run-dev-platform:
	docker compose -f $(COMPOSE_FILE) up -d --wait --wait-timeout 180 rabbitmq mailhog kontiki-registry

down-dev-platform:
	docker compose -f $(COMPOSE_FILE) down

# -----------------------------------------------------------------------------
# Integration tests (Behave)
# -----------------------------------------------------------------------------
# Core suites (CI). Expect run-dev-platform deps already up.
integration-test-core:
	poetry run behave boomerang/services/subscription/tests/integration --stop
	poetry run behave boomerang/services/alert_engine/tests/integration --stop
	poetry run behave boomerang/services/notifiers/email/tests/integration --stop
	poetry run behave boomerang/services/notifiers/telegram/tests/integration --stop
	poetry run behave boomerang/services/notifiers/ntfy/tests/integration --stop

integration-test: run-dev-platform
	@$(MAKE) integration-test-core
	@$(MAKE) integration-test-earthquake-feed

integration-test-subscription: run-dev-platform
	poetry run behave boomerang/services/subscription/tests/integration --stop

integration-test-subscription-tag: run-dev-platform
	poetry run behave boomerang/services/subscription/tests/integration --stop --tags "$(TAG)"

integration-test-email-notifier: run-dev-platform
	poetry run behave boomerang/services/notifiers/email/tests/integration --stop

integration-test-email-notifier-tag: run-dev-platform
	poetry run behave boomerang/services/notifiers/email/tests/integration --stop --tags "$(TAG)"

integration-test-telegram-notifier: run-dev-platform
	poetry run behave boomerang/services/notifiers/telegram/tests/integration --stop

integration-test-telegram-notifier-tag: run-dev-platform
	poetry run behave boomerang/services/notifiers/telegram/tests/integration --stop --tags "$(TAG)"

integration-test-ntfy-notifier: run-dev-platform
	poetry run behave boomerang/services/notifiers/ntfy/tests/integration --stop

integration-test-ntfy-notifier-tag: run-dev-platform
	poetry run behave boomerang/services/notifiers/ntfy/tests/integration --stop --tags "$(TAG)"

integration-test-alert-engine: run-dev-platform
	poetry run behave boomerang/services/alert_engine/tests/integration --stop

integration-test-alert-engine-tag: run-dev-platform
	poetry run behave boomerang/services/alert_engine/tests/integration --stop --tags "$(TAG)"

integration-test-earthquake-feed: run-dev-platform
	poetry run behave boomerang/services/alert_services/earthquake/tests/integration --stop

integration-test-earthquake-feed-tag: run-dev-platform
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

# -----------------------------------------------------------------------------
# Publish one image. One tag per push, so Actions runs one workflow per service.
# make publish-subscription VERSION=1.0.0
# -----------------------------------------------------------------------------
define publish_image
	@test -n "$(VERSION)" || { echo "VERSION is required, e.g. make $@ VERSION=1.0.0" >&2; exit 1; }
	@printf '%s' "$(VERSION)" | grep -Eq '^[0-9]+\.[0-9]+\.[0-9]+$$' || { echo "VERSION must be x.y.z, got: $(VERSION)" >&2; exit 1; }
	git tag $(1)/$(VERSION)
	git push origin $(1)/$(VERSION)
endef

publish-subscription:
	$(call publish_image,subscription)

publish-alert-engine:
	$(call publish_image,alert-engine)

publish-email-notifier:
	$(call publish_image,email-notifier)

publish-telegram-notifier:
	$(call publish_image,telegram-notifier)

publish-ntfy-notifier:
	$(call publish_image,ntfy-notifier)
