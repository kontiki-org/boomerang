# Email Notifier Service

`email-notifier-service` resolves email destinations and delivers notifications
for the email channel.

## What it does

- Load email endpoints from YAML (`app.endpoints`) and/or SQLite.
- Expose the email channel catalog (`get_notification_channel_catalog`).
- Consume `email.alerting.notification.requested`.
- Resolve destination using configured `endpoint_key` (YAML first, else SQLite).
- Send email through configured SMTP.
- Publish delivery outcomes:
  - `alerting.notification.delivered`
  - `alerting.notification.failed`

## Implemented event flow

Consumes:

- `email.alerting.notification.requested`

Behavior:

- parse payload as `NotificationRequest`,
- resolve address from configured / SQLite endpoint,
- send via SMTP,
- publish delivered or failed outcome.
