# Telegram Notifier Service

`telegram-notifier-service` resolves Telegram destinations and delivers
notifications for the telegram channel. With `app.sentinel`, it also holds
external watchdogs and sends `DOWN {name}` / `RECOVERED {name}` on Telegram.

HTTP serves `POST /watchdogs/{name}/heartbeat`. Without `app.sentinel` that
route answers 404. Health in Compose stays the Kontiki registry live probe.

## What it does

- Load Telegram endpoints from YAML (`app.endpoints`).
- Expose the telegram channel catalog (RPC `get_notification_channel_catalog`).
- Consume `telegram.alerting.notification.requested`.
- Resolve destination using configured `endpoint_key`.
- Format alert notifications as structured HTML (shared parsing with email via
  `notifiers.common.structured_alert`).
- Send via Telegram Bot API.
- When `app.sentinel` is set, accept watchdog heartbeats and send a title-only
  `DOWN` / `RECOVERED` message on the watchdog’s endpoint.
- Mark the instance degraded on repeated API failures (`@degraded_on`);
  alert-delivery failures surface through Kontiki exception / alerting.

## Stack E2E

1. Copy `stack/notifiers/telegram_bot_token.yaml.example` to
   `stack/notifiers/telegram_bot_token.yaml` (gitignored) and set your bot token:

   ```yaml
   app:
     telegram:
       bot_token: "123456789:YOUR_BOT_TOKEN_FROM_BOTFATHER"
   ```

   That file is merged on top of `stack/notifiers/telegram.yaml` at startup.

2. Declare endpoints in `stack/notifiers/telegram.yaml` (`app.endpoints`) and
   subscriptions (core: `stack/subscription.yaml`; demo overlay:
   `stack/subscription.demo.yaml`).

3. Start the stack:

   ```bash
   make stack-up
   # or make stack-up-demo for the earthquake producer + sample subscription
   ```

Events:

- consume `telegram.alerting.notification.requested`
- send via Bot API (failures propagate as Kontiki exceptions)

## Message formatting

Alert notifications are rendered as structured HTML messages for Telegram:

- optional category icon from config + banner label from `event_type`
  (humanized; falls back to last category segment when event_type is absent;
  shared with email via `notifiers.common.structured_alert`)
- severity icon (🟢 low → 🔴 critical)
- metadata from `context.data.attributes` in producer insertion order
  (keys humanized: `response_time` → `Response Time`)
- body shown as `Message:` when it differs from the title
- clickable details link when a URL is available

Non-alert messages stay plain text. Watchdog `DOWN` / `RECOVERED` titles are
plain text (`context.kind` = `watchdog`), not structured alerts.

### Category icons (`app.telegram.category_icons`)

Optional map of category key → emoji. Matching is exact, then prefix
(e.g. `weather` matches `weather.wind`). When unset or unmatched, the banner
has no domain emoji (severity icon only).

See [`docs/configuration.md`](../../../../docs/configuration.md) and
[`docs/boomerang-config.example.yaml`](../../../../docs/boomerang-config.example.yaml).

## External sentinel

Optional. `POST /watchdogs/{name}/heartbeat` with `Authorization: Bearer <token>`
refreshes one watchdog. A matching token on a known name answers 204. A missing
or wrong token answers 401. An unknown name, or no `app.sentinel` section,
answers 404.

The message text is `DOWN {name}` or `RECOVERED {name}`, sent through the
endpoint named by `endpoint_key`. The send does not go through the bus.

Keys and state machine: [`docs/configuration.md`](../../../../docs/configuration.md#external-sentinel-appsentinel).
