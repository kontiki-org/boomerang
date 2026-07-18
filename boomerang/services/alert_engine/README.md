# Alert Engine Service

`alert-engine-service` transforms an `alert.normalized` event into
channel-ready notification requests for notifier services.

## What it does

- Consume `alert.normalized`.
- Resolve recipients via RPC `subscription-service.get_recipients_for_alert`.
- Build one `NotificationRequest` per `(recipient_id, channel, endpoint_key)`.
- Publish channel-scoped events:
  - `email.alerting.notification.requested`
  - `sms.alerting.notification.requested`
  - (pattern: `{channel}.alerting.notification.requested`)

## Payload and contract notes

- Outbound payload follows `boomerang_contracts.notification.NotificationRequest`.
- Inbound alerts follow `boomerang_contracts.alert.normalized.NormalizedAlert`.
- Message is built from `title`, `body`, and `context.data` from the normalized alert.
- The full alert (including `attributes`) is sent to
  `get_recipients_for_alert` for subscription matching.

## Current MVP limitations

- Recipient resolution uses only `areas[0]` (single-area behavior).
- The service assumes normalized payload validity is handled upstream by the
  normalization service (no defensive schema validation here).
- If a recipient row has mismatched `channels` / `endpoint_keys` lengths, that
  row is skipped.

## Service boundaries

This service does **not**:

- fetch domain data,
- normalize source payloads,
- send notifications directly (handled by notifier services),
- manage user endpoints (handled by notifier + subscription services).
