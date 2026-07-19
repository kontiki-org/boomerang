# Boomerang – Features

Boomerang is an alerting engine on top of Kontiki. Producers emit normalized
alerts; the core resolves recipients and asks notifiers to deliver.

---

## Pipeline

```text
Producer ──► alert.normalized (AMQP)
         └─► POST /alerts (HTTP, Bearer token)
                    │
                    ▼
              alert-engine
                    │
                    ├── RPC get_recipients_for_alert ──► subscription
                    │
                    └── publish {channel}.alerting.notification.requested
                                    │
                    ┌───────────────┴───────────────┐
                    ▼                               ▼
              email-notifier                 telegram-notifier
                    │                               │
                    └─► alerting.notification.delivered / .failed
```

- **subscription-service** loads subscriptions from YAML, aggregates catalogues,
  and resolves recipients for a given `NormalizedAlert`.
- **alert-engine-service** turns one alert into one `NotificationRequest` per
  `(recipient_id, channel, endpoint_key)`.
- **Notifiers** own endpoint credentials (YAML) and delivery (SMTP / Telegram Bot API).

---

## Ingest

### AMQP

Publish event type `alert.normalized` with a `NormalizedAlert` payload
(see `docs/contracts.md`).

### HTTP

`POST /alerts` on alert-engine (status `202`).

- Auth: `Authorization: Bearer <app.http.token>`
- Body: JSON `NormalizedAlert`
- Same processing path as the AMQP event
- OpenAPI/Swagger is **not** registered for this service unless the route
  declares `version=` (Kontiki docs are version-scoped). Use the curl example
  in the root README.

Local stack: port `8005`, token in `stack/alert_engine.yaml`.

---

## Catalogues

Subscription aggregates:

| Surface | Purpose |
|---------|---------|
| `GET /alert-catalog` (and RPC) | What producers expose (categories, event types, criteria) |
| `GET /notification-channels/catalog` (and RPC) | What channels / endpoint shapes notifiers support |

Connectors are listed under `app.alert_connectors`; notifiers under
`app.notification_channels` (see `stack/subscription.yaml`).

Kontiki **does not deep-merge** list keys across config files: omit
`app.alert_connectors` in the base file and add it only in an overlay
(e.g. `stack/subscription.demo.yaml`), or keep a single source of truth.

---

## Configuration

OSS core is **YAML-only** (no SQLite / interactive CRUD). Declare targeting in
stack config and **restart** services to apply changes.

Stock Compose files list channels and SMTP defaults; they do **not** ship sample
subscriptions or notifier endpoints. Without those, ingest succeeds but nothing
is delivered.

| File | Role |
|------|------|
| `stack/subscription.yaml` | `app.notification_channels` (+ optional `app.subscriptions`) |
| `stack/subscription.demo.yaml` | demo overlay: `app.alert_connectors` |
| `stack/alert_engine.yaml` | ingest token, HTTP |
| `stack/notifiers/email.yaml` | SMTP + optional `app.endpoints` |
| `stack/notifiers/telegram.yaml` | optional `app.endpoints` |
| `stack/notifiers/telegram_bot_token.yaml` | bot token (gitignored; copy from `.example`) |

### Minimal targeting example

Subscription (`stack/subscription.yaml`):

```yaml
app:
  notification_channels:
    - email-notifier-service
  subscriptions:
    demo-owner:
      hello:
        status: active
        subscription:
          rule:
            category: demo
            event_type: "*"
          endpoints:
            - email.inbox
```

Email endpoints (`stack/notifiers/email.yaml`):

```yaml
app:
  endpoints:
    inbox:
      address: you@example.org
```

Endpoint refs in subscriptions are qualified as `<channel>.<endpoint_id>`
(e.g. `email.inbox`, `telegram.ops_alerts`). Matching currently uses
**`areas[0]`** only when area criteria are present (single-area MVP).

---

## Demo producer

`earthquake-feed-service` polls USGS and publishes `alert.normalized`.
Start with `make stack-up-demo` (merges `stack/subscription.demo.yaml` to
register the connector).

Delivery still requires matching `app.subscriptions` plus notifier
`app.endpoints` (and a Telegram bot token for that channel).
