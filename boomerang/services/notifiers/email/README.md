# Email Notifier Service

`email-notifier-service` resolves email destinations and delivers notifications
for the email channel.

Bus-only service: no HTTP entrypoints (health via Kontiki registry when used).

## What it does

- Load email endpoints from YAML (`app.endpoints`).
- Expose the email channel catalog (RPC `get_notification_channel_catalog`).
- Consume `email.alerting.notification.requested`.
- Resolve destination using configured `endpoint_key`.
- Format alert notifications as multipart **plain + HTML** (same structured
  layout as Telegram: event_type banner, humanized attributes, Message when
  body adds info). Subject is the banner label.
- Send email through configured SMTP.
- Mark the instance degraded on repeated SMTP failures (`@degraded_on`);
  delivery failures surface through Kontiki exception / alerting.

## Stack

- Config: `stack/notifiers/email.yaml` (demo ships `app.endpoints.inbox` → MailHog)
- Local SMTP: MailHog (`mailhog:1025`, UI http://127.0.0.1:8025)
- Matching subscriptions: `stack/subscription.yaml` (core) or
  `stack/subscription.demo.yaml` (demo).

## Message formatting

Alert notifications (`context.kind` = `alert` or a non-empty `category`) are
rendered as `multipart/alternative`:

- **Subject**: humanized `event_type` (falls back to last category segment)
- **text/plain**: banner, attribute rows in producer insertion order, optional
  `Message:` when body differs from title, optional Details link
- **text/html**: same layout plus severity icon on the banner

Non-alert messages keep title as subject and title/body as content.

Shared parsing lives in `boomerang.services.notifiers.common.structured_alert`
(also used by the Telegram notifier).

## Event flow

Consumes:

- `email.alerting.notification.requested`

Behavior:

- parse payload as `NotificationRequest`,
- resolve address from configured endpoint,
- format plain + HTML body,
- send via SMTP (failures propagate as Kontiki exceptions).
