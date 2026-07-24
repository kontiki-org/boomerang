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
                    SMTP / Bot API            (delivery only)
```

- **subscription-service** loads subscriptions from YAML, aggregates catalogues,
  and resolves recipients for a given `NormalizedAlert`.
- **alert-engine-service** turns one alert into one `NotificationRequest` per
  `(recipient_id, channel, endpoint_key)`.
- **Notifiers** own endpoint credentials (YAML) and delivery (SMTP / Telegram Bot
  API). Failures surface through Kontiki exception / alerting (no separate
  `alerting.notification.delivered` / `.failed` events).

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

Local stack: port `8005`, token in `stack/alert_engine.yaml`.

---

## Catalogues

Subscription can aggregate discovery catalogues (optional — mainly for a TUI):

| Surface | Purpose |
|---------|---------|
| `GET /alert-catalog` (and RPC) | What producers expose (categories, event types, criteria) |
| `GET /notification-channels/catalog` (and RPC) | What channels / endpoint shapes notifiers support |

Configured via optional `app.alert_connectors` / `app.notification_channels`
(see [`configuration.md`](configuration.md)). Not required for YAML targeting
or delivery.

---

## Configuration

OSS core is **YAML-only** (no SQLite / interactive CRUD). Declare targeting in
stack config and **restart** services to apply changes.

Full `app.*` reference: [`docs/configuration.md`](configuration.md) and
[`docs/boomerang-config.example.yaml`](boomerang-config.example.yaml).
Framework (`kontiki.*`) options are documented in Kontiki.

Core Compose (`make stack-up`) has SMTP defaults and catalogue wiring, but **no**
`app.subscriptions` — ingest succeeds and nothing is delivered until you add
targeting. The demo overlay (`make stack-up-demo`) ships a sample earthquake
subscription plus an email inbox endpoint (MailHog); Telegram still needs a
`chat_id` and bot token.

| File | Role |
|------|------|
| `stack/subscription.yaml` | optional `app.subscriptions` (+ optional catalogue lists) |
| `stack/subscription.demo.yaml` | demo: connector + sample earthquake subscription |
| `stack/alert_engine.yaml` | ingest token, HTTP |
| `stack/notifiers/email.yaml` | SMTP + optional `app.endpoints` (demo ships `inbox`) |
| `stack/notifiers/telegram.yaml` | optional `app.endpoints` (`alerts.chat_id` for demo) |
| `stack/notifiers/telegram_bot_token.yaml` | bot token (gitignored; copy from `.example`) |

### Minimal targeting example

Subscription (`stack/subscription.yaml`):

```yaml
app:
  subscriptions:
    ops:
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

The map under `subscriptions` is **audience → rule id → entry**:
- **audience** (e.g. `ops`) becomes `recipient_id` at dispatch — not an end-user
  account;
- **rule id** (e.g. `hello`) names one targeting rule under that audience (pause
  / enable independently; not sent to notifiers).

Endpoint refs are qualified as `<channel>.<endpoint_id>` (e.g. `email.inbox`,
`telegram.ops_alerts`). Matching uses `category` + `event_type` first;
`criteria` is optional — omit it for a catch-all on attributes (when present,
`all_of` must be non-empty). Area criteria use keys `area.<type>` (e.g.
`area.zone`) against every entry in `alert.areas`.

---

## Demo producer

`earthquake-feed-service` polls USGS and publishes `alert.normalized`.
Start with `make stack-up-demo` (merges `stack/subscription.demo.yaml`).

That overlay registers the connector and an active subscription
(`natural.earthquake` / `earthquake`, `magnitude >= 2`) targeting
`telegram.alerts` and `email.inbox`. Email goes to MailHog via the stock
`inbox` endpoint. For Telegram, set `app.endpoints.alerts.chat_id` and the
bot token overlay.
