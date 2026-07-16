# Boomerang Alert Connector Starter

Get a working alert producer running quickly.

## Quick start

```bash
git clone …   # or open this folder in the monorepo: starters/alert-connector
make install
make start
```

`make start` prints a short message. Copy it into your AI assistant. The assistant follows `AGENTS.md` and `.engineering/` — you do not paste the whole method into the chat.

## Local demo path (email / MailHog)

Official V1 first-experience channel = **email**, observed in **MailHog**.

From this directory:

```bash
make stack-up      # RabbitMQ, MailHog, registry, subscription, alert-engine, email-notifier
make run-local     # connector on the host (leave running)
```

Skeleton only — trigger one pedagogical alert:

```bash
make emit-demo
```

Open MailHog: [http://localhost:8025](http://localhost:8025)  
Expected: mail to `demo@example.org` (subject `Starter demo alert`).

```bash
make stack-logs
make stack-down
```

Host ports: `5672`, `1025`/`8025`, `15672`. Stop any other stack using them before `make stack-up`.

Details: `demo/README.md`.

When an AI generates a **real** connector, it replaces `emit_demo_alert`, updates Behave features, and rewrites `demo/stack/` subscriptions/endpoints to match the new catalog. Telegram / SMS are outside the official first-experience path.

## Tests (AI / maintainers)

```bash
make test          # Behave; used in the generation correction loop
make check-local   # RabbitMQ reachable on localhost:5672
```

## Assumptions

*(Filled when a real connector is generated. Polling connectors use immediate poll + 60s interval as a Starter demo convention.)*

## Next

See `AGENTS.md` if you use an AI assistant. Method details live under `.engineering/` (maintainers / assistants).
