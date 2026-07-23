# Telegram Notifier Service

`telegram-notifier-service` resolves Telegram destinations and delivers
notifications for the telegram channel.

Bus-only service: no HTTP entrypoints (health via Kontiki registry when used).

## What it does

- Load Telegram endpoints from YAML (`app.endpoints`).
- Expose the telegram channel catalog (RPC `get_notification_channel_catalog`).
- Consume `telegram.alerting.notification.requested`.
- Resolve destination using configured `endpoint_key`.
- Send via Telegram Bot API.
- Publish delivery outcomes:
  - `alerting.notification.delivered`
  - `alerting.notification.failed`
- Mark the instance degraded on repeated API failures (`@degraded_on`).

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
   subscriptions in `stack/subscription.yaml`.

3. Start the stack:

   ```bash
   make stack-up
   ```

Events:

- consume `telegram.alerting.notification.requested`
- publish `alerting.notification.delivered` / `alerting.notification.failed`

## Message formatting

Alert notifications are rendered as structured HTML messages for Telegram:

- optional category icon from config + auto label (last category segment, title-case)
- severity icon (🟢 low → 🔴 critical)
- metadata from `context.data.attributes` in producer insertion order
  (keys humanized: `response_time` → `Response Time`)
- body shown as `Message:` when it differs from the title
- clickable details link when a URL is available

Non-alert messages stay plain text.

### Category icons (`app.telegram.category_icons`)

Optional map of category key → emoji. Matching is exact, then prefix
(e.g. `weather` matches `weather.wind`). When unset or unmatched, the banner
has no domain emoji (severity icon only).

See [`docs/configuration.md`](../../../../docs/configuration.md) and
[`docs/boomerang-config.example.yaml`](../../../../docs/boomerang-config.example.yaml).
