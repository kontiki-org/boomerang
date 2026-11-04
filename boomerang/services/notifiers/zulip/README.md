# Zulip

The Zulip notifier delivers each `NotificationRequest` for the zulip channel to `app.zulip.site_url`. The same image can run as an external probe for a Kontiki environment.

Framework options (`kontiki.*`) are documented with Kontiki. Restart the service after a YAML change.

## `app.zulip`

| Key | Default | Description |
|-----|---------|-------------|
| `app.zulip.site_url` | `""` | Zulip site origin, without a trailing path. Required to send. |
| `app.zulip.bot_email` | `""` | Bot email. Required to send. |
| `app.zulip.api_key` | `""` | Bot API key. Required to send. Often supplied via a gitignored overlay (`stack/notifiers/zulip_api_key.yaml`, copied from `stack/notifiers/zulip_api_key.yaml.example`) passed as an extra `--config`. |
| `app.zulip.degraded_after_failures` | `3` | Consecutive API failures before the instance is marked degraded. |
| `app.zulip.category_icons` | unset | Optional map category → emoji for structured alert banners. Exact match, then prefix (for example `weather` matches `weather.wind`). Unmatched categories get no domain emoji. |

### `app.endpoints`

Map of endpoint id → fields. Each endpoint needs `channel` and `topic`. Both are non-empty after trim and at most 60 characters. Spaces are allowed. The topic is the Zulip destination, not the alert title.

```yaml
app:
  zulip:
    site_url: https://chat.example.com
    bot_email: boomerang-bot@chat.example.com
    api_key: ""
    degraded_after_failures: 3
    category_icons:
      natural.earthquake: "🌍"
      weather: "🌧"
      kontiki.registry: "⚙️"
  endpoints:
    alerts:
      channel: ops
      topic: alerts
```

Delivery is a form-encoded `POST` to `{site_url}/api/v1/messages` with `type` `stream`, `to` (the channel), `topic`, and `content`. Authorization is `Basic` over `bot_email:api_key`. A response without `result: success` is a failure.

`content` is Markdown. Structured alerts use built-in severity icons (`low` → 🟢, `moderate` → 🟡, `severe` → 🟠, `critical` → 🔴). The banner title is the humanized `event_type` when present, otherwise the last category segment. Attribute labels are auto-humanized; order follows the producer’s attribute dict. A detail URL becomes a Details link.

The bot must already be a member of the channel and allowed to post. The first send fails when it is not.

## Install

```bash
pip install boomerang-zulip-notifier==1.0.0
```

The package version is the image tag. After install the command is `boomerang-zulip-notifier`.

## Standard mode

The process joins the environment bus and delivers notifications. RabbitMQ and the registry come from `stack/common.services.yaml`.

```bash
docker run --rm \
  -v "$PWD/stack:/stack:ro" \
  ghcr.io/kontiki-org/boomerang-zulip-notifier:1.0.0 \
  --config /stack/common.services.yaml \
  --config /stack/notifiers/zulip.yaml
```

From a checkout:

```bash
poetry run boomerang-zulip-notifier \
  --config stack/common.services.yaml \
  --config stack/notifiers/zulip.yaml
```

## Sentinel mode

The process runs outside the environment and watches its heartbeats. Silence (hosts or RabbitMQ down) sends Down on this channel; the next heartbeat sends Recovered. `kontiki.amqp.disable: true` keeps startup independent of that environment's broker. The Zulip site must stay reachable from this process. The heartbeat route still needs `kontiki.http`.

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

Those alerts use this layout (`category` `kontiki.sentinel`). `event_type` is `down` or `recovered`, so the title is **Down** or **Recovered**. Down is critical, Recovered is low. The heartbeat name is the attribute `watchdog`. There is no message body. They are sent on the notifier’s own delivery path, not on the bus. A failed send is retried on the next sweep. If the watchdog changes state before that send succeeds, only the latest transition is sent.

```yaml
kontiki:
  amqp:
    disable: true
  http:
    address: 0.0.0.0
    port: 8007
app:
  zulip:
    site_url: https://chat.example.com
    bot_email: boomerang-bot@chat.example.com
    api_key: ""
  endpoints:
    ops_alerts:
      channel: ops
      topic: alerts
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
  -p 8007:8007 \
  ghcr.io/kontiki-org/boomerang-zulip-notifier:1.0.0 \
  --config /sentinel.yaml
```

From a checkout:

```bash
poetry run boomerang-zulip-notifier --config sentinel.yaml
```
