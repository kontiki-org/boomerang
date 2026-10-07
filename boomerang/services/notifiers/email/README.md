# Email Notifier Service

`email-notifier-service` resolves email destinations and delivers notifications
for the email channel. With `app.sentinel`, it also holds external watchdogs
and sends `DOWN {name}` / `RECOVERED {name}` by email.

HTTP serves `POST /watchdogs/{name}/heartbeat`. Without `app.sentinel` that
route answers 404. Health in Compose stays the Kontiki registry live probe.

## What it does

- Load email endpoints from YAML (`app.endpoints`).
- Expose the email channel catalog (RPC `get_notification_channel_catalog`).
- Consume `email.alerting.notification.requested`.
- Resolve destination using configured `endpoint_key`.
- Format alert notifications as multipart **plain + HTML** (same structured
  layout as Telegram: event_type banner, humanized attributes, Message when
  body adds info). Subject is the banner label.
- Send email through configured SMTP.
- When `app.sentinel` is set, accept watchdog heartbeats and send a title-only
  `DOWN` / `RECOVERED` mail on the watchdog’s endpoint.
- Mark the instance degraded on repeated SMTP failures (`@degraded_on`);
  alert-delivery failures surface through Kontiki exception / alerting.

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

## External sentinel

Optional. `POST /watchdogs/{name}/heartbeat` with `Authorization: Bearer <token>`
refreshes one watchdog. A matching token on a known name answers 204. A missing
or wrong token answers 401. An unknown name, or no `app.sentinel` section,
answers 404.

`DOWN {name}` and `RECOVERED {name}` are titles only (`context.kind` =
`watchdog`), sent through the endpoint named by `endpoint_key`. They are not
structured alerts and they do not go through the bus.

Keys and state machine: [`docs/configuration.md`](../../../../docs/configuration.md#external-sentinel-appsentinel).
