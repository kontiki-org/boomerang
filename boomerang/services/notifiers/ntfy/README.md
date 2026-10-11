# ntfy

The ntfy notifier publishes each `NotificationRequest` for the ntfy channel to `app.ntfy.server_url`. The same image can run as an external probe for a Kontiki environment.

Framework options (`kontiki.*`) are documented with Kontiki. Restart the service after a YAML change.

## `app.ntfy`

| Key | Default | Description |
|-----|---------|-------------|
| `app.ntfy.server_url` | `https://ntfy.sh` | ntfy base URL. Point this at a self-hosted server. |
| `app.ntfy.token` | `""` | Optional access token sent as `Authorization: Bearer`. Often supplied via a gitignored overlay (`stack/notifiers/ntfy_token.yaml`, copied from `stack/notifiers/ntfy_token.yaml.example`) passed as an extra `--config`. |
| `app.ntfy.degraded_after_failures` | `3` | Consecutive publish failures before the instance is marked degraded. |
| `app.ntfy.category_icons` | unset | Optional map category → emoji, sent as ntfy tags. Exact match, then prefix (for example `weather` matches `weather.wind`). |

### `app.endpoints`

Map of endpoint id → fields. Each endpoint needs `topic` (`[-_A-Za-z0-9]{1,64}`).

```yaml
app:
  ntfy:
    server_url: https://ntfy.sh
    token: ""
    degraded_after_failures: 3
    category_icons:
      natural.earthquake: "🌍"
      weather: "🌧"
      kontiki.registry: "⚙️"
  endpoints:
    alerts:
      topic: your_topic
```

Publish is a JSON `POST` to `{server_url}/` with `topic`, `title`, `message`, `markdown`, and `priority`. Severity maps to ntfy priority (`low` → 2, `moderate` → 3, `severe` → 4, `critical` → 5). A detail URL is sent as `click`. A configured category icon is sent as `tags`.

## Install

```bash
pip install boomerang-ntfy-notifier==1.0.0
```

The package version is the image tag. After install the command is `boomerang-ntfy-notifier`.

## Standard mode

The process joins the environment bus and delivers notifications. RabbitMQ and the registry come from `stack/common.services.yaml`.

```bash
docker run --rm \
  -v "$PWD/stack:/stack:ro" \
  ghcr.io/kontiki-org/boomerang-ntfy-notifier:1.0.0 \
  --config /stack/common.services.yaml \
  --config /stack/notifiers/ntfy.yaml
```

From a checkout:

```bash
poetry run boomerang-ntfy-notifier \
  --config stack/common.services.yaml \
  --config stack/notifiers/ntfy.yaml
```

## Sentinel mode

The process runs outside the environment and watches its heartbeats. Silence (hosts or RabbitMQ down) sends Down on this channel; the next heartbeat sends Recovered. `kontiki.amqp.disable: true` keeps startup independent of that environment's broker. The ntfy server must stay reachable from this process. The heartbeat route still needs `kontiki.http`.

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
    port: 8006
app:
  ntfy:
    server_url: https://ntfy.sh
  endpoints:
    ops_alerts:
      topic: ops_alerts
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
  -p 8006:8006 \
  ghcr.io/kontiki-org/boomerang-ntfy-notifier:1.0.0 \
  --config /sentinel.yaml
```

From a checkout:

```bash
poetry run boomerang-ntfy-notifier --config sentinel.yaml
```
