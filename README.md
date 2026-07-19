# Boomerang

Alerting engine built on [Kontiki](https://github.com/kontiki-org/kontiki).

- **Normalized alerts in, notifications out**: producers publish a
  `NormalizedAlert`; subscription + alert-engine resolve who should be notified;
  email and telegram notifiers deliver.
- **Two ingest paths**: AMQP event `alert.normalized`, or HTTP
  `POST /alerts` on alert-engine (Bearer token).
- **Configuration-driven targeting**: subscriptions and notification endpoints
  live in YAML; catalogues expose what producers and channels support.
- **Contracts package**: shared Pydantic models in `boomerang-contracts`
  (`packages/boomerang-contracts`).

For a detailed overview, see `docs/features.md`.

---

## Quickstart

Start the core stack (RabbitMQ, registry, subscription, alert-engine, email +
telegram notifiers, MailHog):

```bash
make stack-up
```

Useful endpoints after startup:

| What | Where |
|------|--------|
| Subscription HTTP (catalogues) | http://127.0.0.1:8002/api/v1/docs |
| Alert engine `POST /alerts` | http://127.0.0.1:8005/alerts |
| MailHog UI | http://127.0.0.1:8025 |
| RabbitMQ management | http://127.0.0.1:15672 (guest/guest) |

Ingest token for `POST /alerts` is `app.http.token` in
`stack/alert_engine.yaml` (default `change-me`):

```bash
curl -sS -X POST http://127.0.0.1:8005/alerts \
  -H "Authorization: Bearer change-me" \
  -H "Content-Type: application/json" \
  -d '{
    "alert_id": "demo-1",
    "source": "curl",
    "category": "demo",
    "occurred_at": "2026-07-19T12:00:00Z",
    "title": "Hello",
    "body": "Boomerang is up",
    "areas": [{"type": "region", "value": "eu"}]
  }'
```

Delivery only happens when subscriptions and channel endpoints match the alert
(see `stack/*.yaml` and notifier READMEs).

Optional earthquake demo producer:

```bash
make stack-up-demo
```

Stop everything:

```bash
make stack-down
```

> Boomerang relies on RabbitMQ. For Behave / local bus-only deps:
>
> ```bash
> make run-amqp
> ```

---

## Documentation

- Features: `docs/features.md`
- Contracts (payloads & events): `docs/contracts.md`
- Example stack config: `stack/`
- Contributing: `CONTRIBUTING.md`
- License: `LICENSE` (Apache-2.0)

Service-level notes:

| Service | README |
|---------|--------|
| Subscription | `boomerang/services/subscription/README.md` |
| Alert engine | `boomerang/services/alert_engine/README.md` |
| Email notifier | `boomerang/services/notifiers/email/README.md` |
| Telegram notifier | `boomerang/services/notifiers/telegram/README.md` |
| Earthquake feed (demo) | `boomerang/services/alert_services/earthquake/README.md` |
