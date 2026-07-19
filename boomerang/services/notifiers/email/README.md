# Email Notifier Service

`email-notifier-service` resolves email destinations and delivers notifications
for the email channel.

Bus-only service: no HTTP entrypoints (health via Kontiki registry when used).

## What it does

- Load email endpoints from YAML (`app.endpoints`).
- Expose the email channel catalog (RPC `get_notification_channel_catalog`).
- Consume `email.alerting.notification.requested`.
- Resolve destination using configured `endpoint_key`.
- Send email through configured SMTP.
- Publish delivery outcomes:
  - `alerting.notification.delivered`
  - `alerting.notification.failed`
- Mark the instance degraded on repeated SMTP failures (`@degraded_on`).

## Stack

- Config: `stack/notifiers/email.yaml`
- Local SMTP: MailHog (`mailhog:1025`, UI http://127.0.0.1:8025)
- Declare endpoints under `app.endpoints` in that YAML (stock file has SMTP
  only — add endpoints for delivery) and matching subscriptions in
  `stack/subscription.yaml`.

## Event flow

Consumes:

- `email.alerting.notification.requested`

Behavior:

- parse payload as `NotificationRequest`,
- resolve address from configured endpoint,
- send via SMTP,
- publish delivered or failed outcome.
