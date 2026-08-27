# Boomerang – Contracts

Shared models live in the `boomerang-contracts` package
(`packages/boomerang-contracts`). Import as `boomerang_contracts`.

---

## Events

| Event | Payload | Role |
|-------|---------|------|
| `alert.normalized` | `NormalizedAlert` | Producer → alert-engine |
| `{channel}.alerting.notification.requested` | `NotificationRequest` | alert-engine → notifier (`email`, `telegram`, …) |

Notifiers deliver only (SMTP / Bot API). Delivery failures surface through
Kontiki exception / alerting

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
| `recipient_id` | Audience label from YAML subscriptions (first-level key under `app.subscriptions`); not an end-user account. Notifiers route by `endpoint_key`. |
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
```

The root app depends on `boomerang-contracts` from PyPI
(`pip install boomerang-contracts`).

> Note: the package may still export unused CRUD-oriented request models under
> `notification/endpoint.py`. They are **not** part of the OSS YAML targeting
> path; prefer catalogues + YAML config.
