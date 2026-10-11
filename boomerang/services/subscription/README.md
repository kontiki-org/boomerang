# Subscription

Subscription matches each `NormalizedAlert` to the rules in `app.subscriptions` and returns the notifier endpoints that should receive it. A notifier delivers the notification.

Framework options (`kontiki.*`) are documented with Kontiki. Restart the service after a YAML change.

## `app.subscriptions`

Map **rule id → entry**. The rule id (for example `quakes`) names one targeting rule. It is not sent to notifiers. Two rules that resolve to the same endpoint produce one notification. Omitted or `null` means no targeting: ingest succeeds and nothing is delivered.

| Field | Required | Description |
|-------|----------|-------------|
| `category` | yes | Alert category to match (case-insensitive). |
| `event_type` | no | Default `*`. |
| `criteria` | no | Optional list of `{key, operator, value}`. Omit for an attribute catch-all. When present, the list must be non-empty. Every entry must match. `operator` is `eq`, `gte`, `lte`, or `contains`. |
| `endpoints` | yes | Non-empty list of qualified refs `<channel>.<endpoint_id>` (for example `telegram.ops_alerts`, `email.inbox`). |

Matching uses category and event type first, then criteria against alert facts (`severity`, `area.<type>` for each entry in `areas`, and keys from `attributes`).

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

## Catalogues

`app.alert_connectors` and `app.notification_channels` only feed the catalog endpoints (`GET /alert-catalog`, `GET /notification-channels/catalog`, and the matching RPCs). They are not used for matching or delivery.

| Key | Default | Description |
|-----|---------|-------------|
| `app.alert_connectors` | `[]` | Kontiki service names of alert producers. |
| `app.notification_channels` | `[]` | Kontiki service names of notifiers. |

HTTP catalogs listen on port 8002. RabbitMQ and the registry come from `stack/common.services.yaml`.

## Install

```bash
pip install boomerang-subscription==1.0.0
```

The package version is the image tag. After install the command is `boomerang-subscription`.

## Run

```bash
docker run --rm \
  -v "$PWD/stack:/stack:ro" \
  ghcr.io/kontiki-org/boomerang-subscription:1.0.0 \
  --config /stack/common.services.yaml \
  --config /stack/subscription.yaml
```

From a checkout:

```bash
poetry run boomerang-subscription \
  --config stack/common.services.yaml \
  --config stack/subscription.yaml
```
