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
