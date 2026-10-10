# Subscription

Subscription matches each `NormalizedAlert` to the rules in `app.subscriptions` and returns the notifier endpoints that should receive it. A notifier delivers the notification.

## Configure and run

Each rule has an id, a `category`, and a non-empty `endpoints` list of `<channel>.<endpoint_id>` refs. `event_type` defaults to `*`. `criteria` is optional; every entry must match (`eq`, `gte`, `lte`, `contains`). Restart the service after a change. Field reference: [configuration](../../../docs/configuration.md#subscription-service).

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

`app.alert_connectors` and `app.notification_channels` only feed the catalog endpoints. RabbitMQ and the registry come from `stack/common.services.yaml`. HTTP catalogs listen on port 8002.

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
