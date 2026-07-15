# Telegram Notifier Service

`telegram-notifier-service` manages user Telegram endpoints and delivers
notifications for the telegram channel.

## HTTP endpoints

All endpoints authenticated through `identity-service`.

- `POST /endpoints`
- `GET /endpoints`
- `GET /endpoints/{endpoint_key}`
- `DELETE /endpoints/{endpoint_key}`

Storage: SQLite table `telegram_endpoints` keyed by `(user_id, endpoint_key)`.

## Stack E2E

1. Create `stack/telegram_notifier_bot_token.yaml` (gitignored, merged on top of
   `stack/telegram_notifier.yaml` at startup):

   ```yaml
   app:
     telegram:
       bot_token: "123456789:YOUR_BOT_TOKEN_FROM_BOTFATHER"
   ```

2. Start the stack:

   ```bash
   make stack-up
   ```

3. Talk to your bot on Telegram (`/start`), then create a Telegram endpoint in the
   Textual UI (or via subscription HTTP API) with your `chat_id`.

4. Subscribe to an alert connector (e.g. earthquake) on channel `telegram`.

The service listens on port **8004** and publishes/consumes:

- `telegram.alerting.notification.requested`
- `alerting.notification.delivered` / `alerting.notification.failed`
