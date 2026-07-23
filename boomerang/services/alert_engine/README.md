# Alert Engine Service

`alert-engine-service` turns a `NormalizedAlert` into channel-ready
`NotificationRequest` events for notifier services.

## What it does

- Ingest alerts via:
  - AMQP event `alert.normalized`
  - HTTP `POST /alerts` (Bearer token = `app.http.token`)
- Resolve recipients via RPC `subscription-service.get_recipients_for_alert`.
- Build one `NotificationRequest` per `(recipient_id, channel, endpoint_key)`.
- Publish `{channel}.alerting.notification.requested` (e.g.
  `email.alerting.notification.requested`,
  `telegram.alerting.notification.requested`).

## Stack

- Config: `stack/alert_engine.yaml`
- HTTP: port **8005** → `POST /alerts` only (no auto OpenAPI page unless the
  route sets `version=` — Kontiki docs are version-scoped)
- Token: `app.http.token` (default in stack: `change-me`)

## Payload and contract notes

- Inbound: `boomerang_contracts.alert.normalized.NormalizedAlert`
  (validated with Pydantic on both AMQP and HTTP paths).
- Outbound: `boomerang_contracts.notification.message.NotificationRequest`.
- Message `title` / `body` come from the alert; `context.kind` is `"alert"` and
  `context.data` carries `alert_id`, `category`, `event_type`, `severity`,
  `attributes`.
- The full alert is sent to `get_recipients_for_alert` for subscription matching.
