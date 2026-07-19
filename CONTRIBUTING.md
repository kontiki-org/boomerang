# Contributing to Boomerang

This repository follows the same contribution spirit as [Kontiki](https://github.com/kontiki-org/kontiki). For general expectations (maintainer-led model, opening an issue for non-trivial work), see [Contributing to Kontiki](https://github.com/kontiki-org/kontiki/blob/main/CONTRIBUTING.md).

Boomerang is an alerting engine built on Kontiki: producers publish normalized alerts; subscription and alert-engine resolve recipients; notifiers deliver.

For changes in **this repo**, please:

- Open an issue first for non-trivial work and describe the problem, the intended scope, and how it fits Boomerang’s role (contracts, YAML config, bus / `POST /alerts`, notifiers).
- Prefer **small, focused** pull requests with Behave coverage when behavior changes.
- Match existing style (`make fmt`, `make lint`).

## Local checks

```bash
make install
make fmt
make lint
```

Or simply:

```bash
make check
```

## CI

On `main` and pull requests, GitHub Actions runs:

- lint (Python 3.11–3.13)
- core Behave suites (`make integration-test-core`) with RabbitMQ + MailHog +
  kontiki-registry

Earthquake feed Behave stays local-only for now (`make integration-test-earthquake-feed`).

## Integration tests (Behave)

Needs RabbitMQ + MailHog + `kontiki-registry` (heartbeats / degradation
scenarios). `make integration-test` starts them (`run-dev-platform`), then runs
core + earthquake:

```bash
make integration-test
```

Core only (same as CI; platform must already be up):

```bash
make run-dev-platform
make integration-test-core
```

Per service:

```bash
make integration-test-subscription
make integration-test-email-notifier
```

Tear down local deps:

```bash
make down-dev-platform
```

By contributing, you agree your contribution is licensed under the same terms as this project ([Apache License 2.0](LICENSE)).
