# Email

The email notifier delivers each `NotificationRequest` for the email channel over SMTP. The same image can run as an external probe for a Kontiki environment.

Framework options (`kontiki.*`) are documented with Kontiki. Restart the service after a YAML change.

## `app.email`

| Key | Default | Description |
|-----|---------|-------------|
| `app.email.smtp.host` | `localhost` | SMTP host. |
| `app.email.smtp.port` | `25` | SMTP port. |
| `app.email.smtp.use_starttls` | `true` | Enable STARTTLS. |
| `app.email.smtp.username` | `""` | Optional SMTP auth user. |
| `app.email.smtp.password` | `""` | Optional SMTP auth password. |
| `app.email.from.address` | `no-reply@example.org` | From address on outgoing mail. |
| `app.email.degraded_after_failures` | `3` | Consecutive SMTP failures before the instance is marked degraded. |

### `app.endpoints`

Map of endpoint id → fields. Each endpoint needs `address` (destination email).

```yaml
app:
  email:
    smtp:
      host: localhost
      port: 25
      use_starttls: true
      username: ""
      password: ""
    from:
      address: no-reply@example.org
    degraded_after_failures: 3
  endpoints:
    inbox:
      address: you@example.org
```

Alert notifications are sent as multipart plain+HTML. The subject and banner use `event_type` when present, otherwise the category, with humanized attributes.

## Install

```bash
pip install boomerang-email-notifier==1.0.0
```

The package version is the image tag. After install the command is `boomerang-email-notifier`.

## Standard mode

The process joins the environment bus and delivers notifications. RabbitMQ and the registry come from `stack/common.services.yaml`. The stack file points SMTP at MailHog.

```bash
docker run --rm \
  -v "$PWD/stack:/stack:ro" \
  ghcr.io/kontiki-org/boomerang-email-notifier:1.0.0 \
  --config /stack/common.services.yaml \
  --config /stack/notifiers/email.yaml
```

From a checkout:

```bash
poetry run boomerang-email-notifier \
  --config stack/common.services.yaml \
  --config stack/notifiers/email.yaml
```

## Sentinel mode

The process runs outside the environment and watches its heartbeats. Silence (hosts or RabbitMQ down) sends Down on this channel; the next heartbeat sends Recovered. `kontiki.amqp.disable: true` keeps startup independent of that environment's broker. SMTP must stay reachable from this process. The heartbeat route still needs `kontiki.http`.

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

Those alerts use the notifier’s structured layout. `category` is `kontiki.sentinel`. `event_type` is `down` or `recovered`, so the subject and banner are **Down** or **Recovered**. Down is critical, Recovered is low. The heartbeat name is the attribute `watchdog`. There is no message body. They are sent on the notifier’s own delivery path, not on the bus. A failed send is retried on the next sweep. If the watchdog changes state before that send succeeds, only the latest transition is sent.

```yaml
kontiki:
  amqp:
    disable: true
  http:
    address: 0.0.0.0
    port: 8003
app:
  email:
    smtp:
      host: localhost
      port: 25
    from:
      address: no-reply@example.org
  endpoints:
    ops_alerts:
      address: ops@example.org
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
  -p 8003:8003 \
  ghcr.io/kontiki-org/boomerang-email-notifier:1.0.0 \
  --config /sentinel.yaml
```

From a checkout:

```bash
poetry run boomerang-email-notifier --config sentinel.yaml
```
