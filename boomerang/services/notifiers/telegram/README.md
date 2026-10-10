# Telegram

The Telegram notifier delivers each `NotificationRequest` for the telegram channel through the Bot API. The same image can run as an external probe for a Kontiki environment.

## Configure and run

Each endpoint needs a `chat_id`. `app.telegram.bot_token` comes from BotFather. Copy `stack/notifiers/telegram_bot_token.yaml.example` to `stack/notifiers/telegram_bot_token.yaml` and set the token and the chat id. `app.telegram.category_icons` is an optional category-to-emoji map. Field reference: [configuration](../../../../docs/configuration.md#telegram-notifier-service).

### Standard mode

The process joins the environment bus and delivers notifications. RabbitMQ and the registry come from `stack/common.services.yaml`.

```yaml
app:
  telegram:
    bot_token: "123456789:YOUR_BOT_TOKEN_FROM_BOTFATHER"
  endpoints:
    alerts:
      chat_id: "123456789"
```

```bash
docker run --rm \
  -v "$PWD/stack:/stack:ro" \
  ghcr.io/kontiki-org/boomerang-telegram-notifier:1.0.0 \
  --config /stack/common.services.yaml \
  --config /stack/notifiers/telegram.yaml \
  --config /stack/notifiers/telegram_bot_token.yaml
```

From a checkout:

```bash
poetry run boomerang-telegram-notifier \
  --config stack/common.services.yaml \
  --config stack/notifiers/telegram.yaml \
  --config stack/notifiers/telegram_bot_token.yaml
```

### Sentinel mode

The process runs outside the environment and watches its heartbeats. Silence (hosts or RabbitMQ down) sends Down on this channel; the next heartbeat sends Recovered. `kontiki.amqp.disable: true` keeps startup independent of that environment's broker. `POST /watchdogs/{name}/heartbeat` listens on the HTTP port. Keys: [configuration](../../../../docs/configuration.md#external-sentinel-appsentinel).

```yaml
kontiki:
  amqp:
    disable: true
  http:
    address: 0.0.0.0
    port: 8004
app:
  telegram:
    bot_token: "123456789:YOUR_BOT_TOKEN_FROM_BOTFATHER"
  endpoints:
    ops_alerts:
      chat_id: "123456789"
  sentinel:
    state_path: /var/lib/boomerang/sentinel-state.json
    sweep_seconds: 10
    watchdogs:
      prod:
        token: "change-me"
        timeout_seconds: 180
        endpoint_key: ops_alerts
```

```bash
docker run --rm \
  -v "$PWD/sentinel.yaml:/sentinel.yaml:ro" \
  -v "$PWD/sentinel-state:/var/lib/boomerang" \
  -p 8004:8004 \
  ghcr.io/kontiki-org/boomerang-telegram-notifier:1.0.0 \
  --config /sentinel.yaml
```

From a checkout:

```bash
poetry run boomerang-telegram-notifier --config sentinel.yaml
```
