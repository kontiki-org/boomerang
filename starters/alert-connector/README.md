# Boomerang Alert Connector Starter

Get a working alert producer running quickly.

## Quick start

```bash
git clone …   # or open this folder in the monorepo: starters/alert-connector
make install
make start
```

`make start` prints a short message. Copy it into your AI assistant. The assistant follows `AGENTS.md` and `.engineering/` — you do not paste the whole method into the chat.

## Run locally

```bash
make check-local   # RabbitMQ on localhost:5672
make test
make run-local
```

This starter runs **only the connector**. It does not start Boomerang or RabbitMQ.

From the Boomerang monorepo, start a stack that includes MailHog (official V1 demo channel = **email**):

```bash
make stack-embedded-up
# or: make stack-up
```

Open MailHog at [http://localhost:8025](http://localhost:8025) to see demo notifications.
Other channels (Telegram, SMS, …) are outside the official first-experience path.

The pedagogical RPC `emit_demo_alert` (demo skeleton only) is replaced when you generate a real connector.

## Assumptions

*(Filled when a real connector is generated. Polling connectors use immediate poll + 60s interval as a Starter demo convention.)*

## Next

See `AGENTS.md` if you use an AI assistant. Method details live under `.engineering/` (maintainers / assistants).
