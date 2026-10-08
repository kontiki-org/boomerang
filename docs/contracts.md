# Boomerang – Contracts

Shared models live in the `boomerang-contracts` package
(`packages/boomerang-contracts`). Import as `boomerang_contracts`.

---

## Events

| Event | Payload | Role |
|-------|---------|------|
| `alert.normalized` | `NormalizedAlert` | Producer → alert-engine |
| `{channel}.alerting.notification.requested` | `NotificationRequest` | alert-engine → notifier (`email`, `telegram`, …) |

Notifiers deliver `NotificationRequest` events (SMTP / Bot API). Delivery
failures surface through Kontiki exception / alerting. Watchdog Down /
Recovered alerts are built by the notifier and sent on that same delivery
path; they are not bus events. `message.context.kind` is `alert`, and
`message.context.data` is `category` `kontiki.sentinel`, `event_type` `down`
or `recovered`, `severity` `critical` or `low`, and attribute `watchdog` (the
heartbeat name). The banner and the email subject are **Down** or
**Recovered**.

Constant for the ingest event:

```python
from boomerang_contracts.alert.normalized import ALERT_NORMALIZED_EVENT
# "alert.normalized"
```

---

## `NormalizedAlert`

```python
from boomerang_contracts.alert.normalized import NormalizedAlert, AlertArea
```

| Field | Notes |
|-------|--------|
| `schema_version` | default `"1.0"` |
| `alert_id` | required |
| `source` | required |
| `category` | required (normalized lower) |
| `event_type` | default `"*"` |
| `severity` | default `"unknown"` |
| `occurred_at` | datetime |
| `title` / `body` | required |
| `areas` | list of `{type, value}` |
| `attributes` | free-form dict (keys lowercased) |
| `expires_at` | optional |

Extra fields are forbidden (`extra="forbid"`).

---

## `NotificationRequest`

```python
from boomerang_contracts.notification.message import NotificationRequest
```

| Field | Notes |
|-------|--------|
| `channel` | e.g. `email`, `telegram` |
| `endpoint_key` | notifier endpoint id (from qualified ref `<channel>.<endpoint_id>`) |
| `message` | `title`, `body`, `context` (`kind` + `data`) |

Built by alert-engine from the normalized alert and subscription match rows.

---

## Catalogues

Alert subscription catalogue models:
`boomerang_contracts.alert.catalog` (criteria, event types, categories).

Notification channel catalogue models:
`boomerang_contracts.notification.channel_catalog`.

RPC name used by connectors:

```python
from boomerang_contracts.alert.catalog import GET_ALERT_SUBSCRIPTION_CATALOG_RPC
# "get_alert_subscription_catalog"
```

---

## Package layout (public surface)

```text
packages/boomerang-contracts/
  src/boomerang_contracts/
    alert/normalized.py
    alert/catalog.py
    notification/message.py
    notification/channel_catalog.py
    notification/validation.py
```

Stable surface: `NormalizedAlert`, catalogues, `NotificationRequest`,
`validate_endpoint_fields`, `endpoint_display`. Targeting is YAML-only
(`app.subscriptions`, notifier `app.endpoints`).

Published `kontiki-boomerang` depends on `boomerang-contracts` from PyPI
(`pip install boomerang-contracts`).
