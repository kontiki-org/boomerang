# Boomerang configuration reference

Boomerang services are Kontiki services. Framework options live under **`kontiki`**
(see Kontiki’s `docs/configuration.md`). Application settings for Boomerang live
under **`app`**.

Each process loads **its own** YAML (Compose merges `stack/common.services.yaml`
with the service file under `stack/`). Keys below apply only to the service that
reads them.

An annotated example covering every `app.*` option is in
[boomerang-config.example.yaml](boomerang-config.example.yaml). Runtime stack
files live under [`stack/`](../stack/).

---

## subscription-service

| Key | Default | Description |
|-----|---------|-------------|
| `app.subscriptions` | unset (`{}` behaviour) | YAML subscription store. See below. Omitted / `null` → no targeting (ingest succeeds, nothing is delivered). |
| `app.alert_connectors` | `[]` | Optional. Kontiki service names of alert producers. **Catalogue aggregation only** (RPC/HTTP alert catalog for a TUI or similar) — not used for alert matching or delivery. |
| `app.notification_channels` | `[]` | Optional. Kontiki service names of notifiers. **Catalogue aggregation only** (RPC/HTTP notification-channels catalog for a TUI or similar) — not used for matching or delivery. |

### `app.subscriptions`

Map **rule id → entry**. Restart the service after changes.

The rule id (e.g. `quakes`, `registry-down`) names one targeting rule. It is not
sent to notifiers. Two rules that resolve to the same endpoint produce one
notification.

| Field | Required | Description |
|-------|----------|-------------|
| `category` | yes | Alert category to match (case-insensitive). |
| `event_type` | no | Default `*`. |
| `criteria` | no | Optional list of `{key, operator, value}`. Omit for attribute catch-all. When present, the list must be non-empty. Every entry must match. `operator` is `eq`, `gte`, `lte`, or `contains`. |
| `endpoints` | yes | Non-empty list of qualified refs `<channel>.<endpoint_id>` (e.g. `telegram.ops_alerts`, `email.inbox`). |

Matching uses category + event type first, then criteria against alert facts
(`severity`, `area.<type>` for each entry in `areas`, and keys from `attributes`).

Example:

```yaml
app:
  subscriptions:
    quakes:
      category: natural.earthquake
      event_type: "*"
      criteria:
        - key: magnitude
          operator: gte
          value: 4.5
      endpoints:
        - telegram.ops_alerts
```

---

## alert-engine-service

| Key | Default | Description |
|-----|---------|-------------|
| `app.http.token` | `""` | Bearer token for `POST /alerts`. Empty → HTTP ingest rejects as unauthorized. |

Recipients are resolved via RPC to `subscription-service` (fixed service name).

---

## email-notifier-service

| Key | Default | Description |
|-----|---------|-------------|
| `app.email.smtp.host` | `localhost` | SMTP host. |
| `app.email.smtp.port` | `25` | SMTP port. |
| `app.email.smtp.use_starttls` | `true` | Enable STARTTLS. |
| `app.email.smtp.username` | `""` | Optional SMTP auth user. |
| `app.email.smtp.password` | `""` | Optional SMTP auth password. |
| `app.email.from.address` | `no-reply@example.org` | From address on outgoing mail. |
| `app.email.degraded_after_failures` | `3` | Consecutive SMTP failures before the instance is marked degraded. |
| `app.endpoints` | unset | Map of endpoint_id → fields. See below. |

### `app.endpoints` (email)

Each endpoint must match the email channel catalogue: required field `address`
(destination email).

```yaml
app:
  endpoints:
    inbox:
      address: you@example.org
```

Alert notifications are sent as multipart plain+HTML with an `event_type` (or
category) subject/banner and humanized attributes — same structured layout as
Telegram (see the email notifier README).

Optional external sentinel: [`app.sentinel`](#external-sentinel-appsentinel).

---

## telegram-notifier-service

| Key | Default | Description |
|-----|---------|-------------|
| `app.telegram.bot_token` | `""` | BotFather token. Required to send. Often supplied via a gitignored overlay (see `stack/notifiers/telegram_bot_token.yaml.example`). |
| `app.telegram.api_base_url` | `https://api.telegram.org` | Telegram Bot API base URL (override for mocks). |
| `app.telegram.degraded_after_failures` | `3` | Consecutive API failures before the instance is marked degraded. |
| `app.telegram.category_icons` | unset | Optional map category → emoji for structured alert banners. Exact match, then prefix (e.g. `weather` matches `weather.wind`). Unmatched → no domain emoji. |
| `app.endpoints` | unset | Map of endpoint_id → fields. See below. |

### `app.endpoints` (telegram)

Each endpoint must match the telegram channel catalogue: required field
`chat_id` (digits, optional leading `-`).

```yaml
app:
  endpoints:
    ops_alerts:
      chat_id: "123456789"
```

### `app.telegram.category_icons`

```yaml
app:
  telegram:
    category_icons:
      natural.earthquake: "🌍"
      weather: "🌧"
      kontiki.registry: "⚙️"
```

Structured messages also use built-in severity icons (`low` → 🟢 … `critical` → 🔴).
The banner title is the humanized `event_type` when present, otherwise the last
category segment. Attribute labels are auto-humanized; order follows the
producer’s attribute dict.
See [`boomerang/services/notifiers/telegram/README.md`](../boomerang/services/notifiers/telegram/README.md).

Optional external sentinel: [`app.sentinel`](#external-sentinel-appsentinel).

---

## ntfy-notifier-service

| Key | Default | Description |
|-----|---------|-------------|
| `app.ntfy.server_url` | `https://ntfy.sh` | ntfy base URL. Point this at a self-hosted server. Override for tests. |
| `app.ntfy.token` | `""` | Optional access token sent as `Authorization: Bearer`. Often supplied via a gitignored overlay (see `stack/notifiers/ntfy_token.yaml.example`). |
| `app.ntfy.degraded_after_failures` | `3` | Consecutive publish failures before the instance is marked degraded. |
| `app.ntfy.category_icons` | unset | Optional map category → emoji, sent as ntfy tags. Exact match, then prefix (e.g. `weather` matches `weather.wind`). |
| `app.endpoints` | unset | Map of endpoint_id → fields. See below. |

### `app.endpoints` (ntfy)

Each endpoint must match the ntfy channel catalogue: required field `topic`
(`[-_A-Za-z0-9]{1,64}`).

```yaml
app:
  endpoints:
    ops_alerts:
      topic: ops_alerts
```

Publish is a JSON `POST` to `{server_url}/` with `topic`, `title`, `message`,
`markdown`, and `priority`. Severity maps to ntfy priority (`low` → 2,
`moderate` → 3, `severe` → 4, `critical` → 5). A detail URL is sent as `click`.
A configured category icon is sent as `tags`. Watchdog Down and Recovered
alerts use this layout (`category` `kontiki.sentinel`).

### `app.ntfy.category_icons`

```yaml
app:
  ntfy:
    category_icons:
      natural.earthquake: "🌍"
      weather: "🌧"
      kontiki.registry: "⚙️"
```

See [`boomerang/services/notifiers/ntfy/README.md`](../boomerang/services/notifiers/ntfy/README.md).

Optional external sentinel: [`app.sentinel`](#external-sentinel-appsentinel).

---

## External sentinel (`app.sentinel`)

Optional on **email-notifier-service**, **telegram-notifier-service**, and
**ntfy-notifier-service**. Same keys on each service. One notifier, in another failure domain, holds the
watchdogs for a Kontiki environment that only emits outbound heartbeats.

Omit the section on a notifier that only delivers alerts. `POST
/watchdogs/{name}/heartbeat` then answers **404**, and no sweep runs.

| Key | Default | Description |
|-----|---------|-------------|
| `app.sentinel.state_path` | required | JSON file for watchdog state. Missing file on first start is the initial unseen state. An unreadable file fails startup. |
| `app.sentinel.sweep_seconds` | `1` | How often the process applies timeouts and retries an outbound `DOWN` / `RECOVERED`. |
| `app.sentinel.watchdogs` | `{}` | Map of watchdog name → spec. The name is the `{name}` in the heartbeat URL. |

### `app.sentinel.watchdogs.<name>`

| Field | Required | Description |
|-------|----------|-------------|
| `token` | yes | Expected `Authorization: Bearer` value. |
| `timeout_seconds` | yes | Silence after which the watchdog is DOWN. Ops rule: at least three times the monitor’s send interval. |
| `endpoint_key` | yes | Key in this notifier’s `app.endpoints`. An unknown key fails startup. |

```yaml
app:
  endpoints:
    ops_alerts:
      chat_id: "123456789"   # or address: ops@example.org on email, or topic: ops_alerts on ntfy
  sentinel:
    state_path: /var/lib/boomerang/sentinel-state.json
    sweep_seconds: 1
    watchdogs:
      prod:
        token: "change-me"
        timeout_seconds: 180
        endpoint_key: ops_alerts
```

`POST /watchdogs/{name}/heartbeat` (empty body):

| Case | Status |
|------|--------|
| Known name, matching Bearer | 204 |
| Known name, missing or wrong Bearer | 401 |
| Unknown name, or no `app.sentinel` section | 404 |

A watchdog is unseen, UP, or DOWN. The first heartbeat before
`timeout_seconds` marks it UP and sends nothing. No heartbeat, or a last
heartbeat older than `timeout_seconds`, sends a Down alert. A heartbeat
received while DOWN sends a Recovered alert. The state file keeps a DOWN
watchdog across a restart.

Those alerts use the notifier’s structured layout (`category`
`kontiki.sentinel`, `event_type` `down` or `recovered`, attribute `watchdog`).
Down is critical, Recovered is low. They are sent
on the notifier’s own delivery path, not on the bus. A failed send is retried
on the next sweep. If the watchdog changes state before that send succeeds,
only the latest transition is sent.

A sentinel outside the monitored environment sets `kontiki.amqp.disable: true`
so startup does not require that environment’s broker. The heartbeat route
still needs `kontiki.http`.

---

## earthquake-feed-service (demo producer)

| Key | Default | Description |
|-----|---------|-------------|
| `app.earthquake.usgs.feed_url` | USGS `2.5_hour` GeoJSON URL | Feed URL to poll. |
| `app.earthquake.min_magnitude` | `2.5` | Ignore events below this magnitude. |
| `app.earthquake.dedupe_max_ids` | `5000` | Max remembered event ids for dedupe. |
| `app.earthquake.alert_ttl_hours` | `6` | TTL stamped on published alerts. |
| `app.earthquake.http_timeout_seconds` | `30` | HTTP timeout when fetching the feed. |
| `app.earthquake.category` | `natural.earthquake` | Category set on published `NormalizedAlert` payloads. |

Publishes `alert.normalized` on its own; no subscription-service list is required
for delivery.
