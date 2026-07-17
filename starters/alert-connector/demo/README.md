# Demo environment (not the connector)

YAML under `stack/` configures the autonomous Docker Compose stack started by `make stack-up`:

- RabbitMQ, MailHog
- `kontiki-registry` — Kontiki platform plumbing (registration / heartbeats), **not** an alert source
- subscription, alert-engine, email-notifier
- Declarative email endpoints and subscriptions

The connector (`make run-local`) does **not** create subscriptions or endpoints.

## Subscription rule (skeleton)

Canonical template: `stack/subscription.skeleton.yaml` (`demo.starter` / `demo_alert` → `email.demo_inbox`).

`stack/subscription.yaml` is a **working copy** (gitignored). The AI overwrites it when generating a connector. To reset the kit skeleton:

```bash
cp demo/stack/subscription.skeleton.yaml demo/stack/subscription.yaml
```

## Commands

```bash
make stack-up
make run-local      # other terminal
make stack-down     # after generation updated subscription.yaml — then stack-up again to demo
make stack-logs
```

`demo/stack/` YAML is loaded only when services start. After the AI updates `subscription.yaml`: **`make stack-down`**, then **`make stack-up`** + **`make run-local`** for a clean demo.

MailHog UI: http://localhost:8025

Host ports: `5672` (AMQP), `1025`/`8025` (MailHog), `15672` (RabbitMQ UI).  
Stop any other Boomerang stack using those ports before `make stack-up`.
