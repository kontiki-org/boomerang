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
- HTTP: port **8005** → `POST /alerts` (docs at `/api/v1/docs`)
- Token: `app.http.token` (default in stack: `change-me`)

## Payload and contract notes

- Inbound: `boomerang_contracts.alert.normalized.NormalizedAlert`
  (validated with Pydantic on both AMQP and HTTP paths).
- Outbound: `boomerang_contracts.notification.message.NotificationRequest`.
- Message `title` / `body` come from the alert; `context.kind` is `"alert"` and
  `context.data` carries `alert_id`, `category`, `event_type`, `severity`,
  `attributes`.
- The full alert is sent to `get_recipients_for_alert` for subscription matching.

## Current MVP limitations

- Area matching lives in subscription-service and uses only `areas[0]`.
- Rows missing `recipient_id` / `channel` / `endpoint_key` are skipped.

## Service boundaries

This service does **not**:

- fetch domain data,
- normalize source payloads from upstream APIs,
- send notifications directly (handled by notifier services),
- manage user endpoints (handled by notifiers + subscription config).
