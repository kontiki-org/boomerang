# Boomerang Alert Connector Starter

Get a working alert producer running quickly.

## Quick start

```bash
git clone …   # or open this folder in the monorepo: starters/alert-connector
make install
make start
```

`make start` prints a short message. Copy it into your AI assistant. The assistant follows `AGENTS.md` and `.engineering/` — you do not paste the whole method into the chat.

Then, when you want to run the demo connector locally:

```bash
make check-local   # RabbitMQ on localhost:5672
make test
make run-local
```

This starter runs **only the connector**. It does not start Boomerang or RabbitMQ.

From the Boomerang monorepo:

```bash
make stack-embedded-up
# or: make stack-up / make run-dev-platform
```

The demo exposes pedagogical RPC `emit_demo_alert` (not for real connectors) on service `alert-connector-demo-service`.

## Assumptions

*(Filled when a real connector is generated.)*

## Next

See `AGENTS.md` if you use an AI assistant. Method details live under `.engineering/` (maintainers / assistants).
