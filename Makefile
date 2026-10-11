.PHONY: \
	install fmt lint check clean \
	integration-test integration-test-core \
	integration-test-subscription integration-test-subscription-tag \
	integration-test-email-notifier integration-test-email-notifier-tag \
	integration-test-telegram-notifier integration-test-telegram-notifier-tag \
	integration-test-ntfy-notifier integration-test-ntfy-notifier-tag \
	integration-test-alert-engine integration-test-alert-engine-tag \
	run-dev-platform down-dev-platform \
	stack-up stack-down stack-build stack-rebuild \
	run-service \
	publish-subscription publish-alert-engine \
	publish-email-notifier publish-telegram-notifier publish-ntfy-notifier \
	build-service-package

PY ?= poetry run python
COMPOSE_FILE ?= docker-compose.dev.yaml
STACK_COMPOSE_FILE ?= docker-compose.stack.yaml
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

# -----------------------------------------------------------------------------
# Local stack (core alerting runtime)
# -----------------------------------------------------------------------------
stack-build:
	docker compose -f $(STACK_COMPOSE_FILE) build

stack-rebuild:
	docker compose -f $(STACK_COMPOSE_FILE) build --no-cache

stack-up:
	docker compose -f $(STACK_COMPOSE_FILE) up -d --build --wait --wait-timeout 180

stack-down:
	docker compose -f $(STACK_COMPOSE_FILE) down

run-service:
	poetry run boomerang-subscription --config config.example.yaml

# -----------------------------------------------------------------------------
# Tag service/VERSION. Actions publishes the GHCR image and the PyPI package
# boomerang-<service> at that version.
# make publish-subscription VERSION=1.0.1
#
# Build a wheel locally (does not publish). SOURCE_REF reads that tag's tree
# so an existing image tag can get a matching package without a rebuild.
# make build-service-package SERVICE=telegram-notifier VERSION=1.0.0 \
#     SOURCE_REF=telegram-notifier/1.0.0
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

build-service-package:
	@test -n "$(SERVICE)" || { echo "SERVICE is required, e.g. make $@ SERVICE=telegram-notifier VERSION=1.0.0" >&2; exit 1; }
	@test -n "$(VERSION)" || { echo "VERSION is required, e.g. make $@ SERVICE=telegram-notifier VERSION=1.0.0" >&2; exit 1; }
	SERVICE="$(SERVICE)" VERSION="$(VERSION)" SOURCE_REF="$(SOURCE_REF)" python3 .github/scripts/build_service_wheel.py
