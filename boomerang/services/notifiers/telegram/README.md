# Telegram

The Telegram notifier delivers each `NotificationRequest` for the telegram channel through the Bot API. The same image can run as an external probe for a Kontiki environment.

Framework options (`kontiki.*`) are documented with Kontiki. Restart the service after a YAML change.

## `app.telegram`

| Key | Default | Description |
|-----|---------|-------------|
| `app.telegram.bot_token` | `""` | BotFather token. Required to send. Often supplied via a gitignored overlay (`stack/notifiers/telegram_bot_token.yaml`, copied from `stack/notifiers/telegram_bot_token.yaml.example`). |
| `app.telegram.api_base_url` | `https://api.telegram.org` | Telegram Bot API base URL. |
| `app.telegram.degraded_after_failures` | `3` | Consecutive API failures before the instance is marked degraded. |
| `app.telegram.category_icons` | unset | Optional map category → emoji for structured alert banners. Exact match, then prefix (for example `weather` matches `weather.wind`). Unmatched categories get no domain emoji. |

### `app.endpoints`

Map of endpoint id → fields. Each endpoint needs `chat_id` (digits, optional leading `-`).

```yaml
app:
  telegram:
    bot_token: "123456789:YOUR_BOT_TOKEN_FROM_BOTFATHER"
    category_icons:
      natural.earthquake: "🌍"
      weather: "🌧"
      kontiki.registry: "⚙️"
  endpoints:
    alerts:
      chat_id: "123456789"
```

Structured messages use built-in severity icons (`low` → 🟢 … `critical` → 🔴). The banner title is the humanized `event_type` when present, otherwise the last category segment. Attribute labels are auto-humanized; order follows the producer’s attribute dict.

## Install

```bash
pip install boomerang-telegram-notifier==1.0.0
```

The package version is the image tag. After install the command is `boomerang-telegram-notifier`.

## Standard mode

The process joins the environment bus and delivers notifications. RabbitMQ and the registry come from `stack/common.services.yaml`.

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

## Sentinel mode

The process runs outside the environment and watches its heartbeats. Silence (hosts or RabbitMQ down) sends Down on this channel; the next heartbeat sends Recovered. `kontiki.amqp.disable: true` keeps startup independent of that environment's broker. The heartbeat route still needs `kontiki.http`.

Omit `app.sentinel` on a notifier that only delivers alerts. `POST /watchdogs/{name}/heartbeat` then answers **404**, and no sweep runs.

| Key | Default | Description |
|-----|---------|-------------|
| `app.sentinel.state_path` | required | JSON file for watchdog state. A missing file on first start is the initial unseen state. An unreadable file fails startup. |
| `app.sentinel.sweep_seconds` | `1` | How often the process applies timeouts and retries a pending Down or Recovered alert. |
| `app.sentinel.watchdogs` | `{}` | Map of watchdog name → spec. The name is the `{name}` in the heartbeat URL. |

### `app.sentinel.watchdogs.<name>`

| Field | Required | Description |
|-------|----------|-------------|
| `token` | yes | Expected `Authorization: Bearer` value. |
| `timeout_seconds` | yes | Silence after which the watchdog is DOWN. At least three times the monitor’s send interval. |
| `endpoint_key` | yes | Key in this notifier’s `app.endpoints`. An unknown key fails startup. |

`POST /watchdogs/{name}/heartbeat` (empty body):

| Case | Status |
|------|--------|
| Known name, matching Bearer | 204 |
| Known name, missing or wrong Bearer | 401 |
| Unknown name, or no `app.sentinel` section | 404 |

A watchdog is unseen, UP, or DOWN. The first heartbeat before `timeout_seconds` marks it UP and sends nothing. No heartbeat, or a last heartbeat older than `timeout_seconds`, sends a Down alert. A heartbeat received while DOWN sends a Recovered alert. The state file keeps a DOWN watchdog across a restart.

Those alerts use the notifier’s structured layout. `category` is `kontiki.sentinel`. `event_type` is `down` or `recovered`, so the banner is **Down** or **Recovered**. Down is critical, Recovered is low. The heartbeat name is the attribute `watchdog`. There is no message body. They are sent on the notifier’s own delivery path, not on the bus. A failed send is retried on the next sweep. If the watchdog changes state before that send succeeds, only the latest transition is sent.

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
