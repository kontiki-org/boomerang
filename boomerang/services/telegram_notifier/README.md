# Telegram Notifier Service

`telegram-notifier-service` resolves Telegram destinations and delivers
notifications for the telegram channel.

## What it does

- Load Telegram endpoints from YAML (`app.endpoints`) and/or SQLite.
- Expose the telegram channel catalog (`get_notification_channel_catalog`).
- Consume `telegram.alerting.notification.requested`.
- Resolve destination using configured `endpoint_key` (YAML first, else SQLite).
- Send via Telegram Bot API.
- Publish delivery outcomes:
  - `alerting.notification.delivered`
  - `alerting.notification.failed`

## Stack E2E

1. Create `stack/telegram_notifier_bot_token.yaml` (gitignored, merged on top of
   `stack/telegram_notifier.yaml` at startup):

   ```yaml
   app:
     telegram:
       bot_token: "123456789:YOUR_BOT_TOKEN_FROM_BOTFATHER"
   ```

2. Declare endpoints in `stack/telegram_notifier.yaml` (`app.endpoints`) and
   subscriptions in `stack/subscription.yaml`.

3. Start the stack:

   ```bash
   make stack-up
   ```

The service listens on port **8004** and publishes/consumes:

- `telegram.alerting.notification.requested`
- `alerting.notification.delivered` / `alerting.notification.failed`

## Message formatting

Alert notifications are rendered as structured HTML messages for Telegram:

- category icon and label (e.g. 🌍 Earthquake)
- severity icon (🟢 low → 🔴 critical)
- optional metadata from `context.data.attributes` (magnitude, location, etc.)
- clickable details link when a URL is available

Non-alert messages stay plain text.
