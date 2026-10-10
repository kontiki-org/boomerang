# Alert engine

The alert engine accepts a `NormalizedAlert` from the bus or from `POST /alerts`, asks subscription for the recipients, and publishes one `NotificationRequest` per endpoint.

## Configure and run

`POST /alerts` expects `Authorization: Bearer` set to `app.http.token`. HTTP listens on port 8005. Field reference: [configuration](../../../docs/configuration.md#alert-engine-service).

```yaml
app:
  http:
    token: "change-me"
```

RabbitMQ and the registry come from `stack/common.services.yaml`.

```bash
docker run --rm \
  -v "$PWD/stack:/stack:ro" \
  ghcr.io/kontiki-org/boomerang-alert-engine:1.0.0 \
  --config /stack/common.services.yaml \
  --config /stack/alert_engine.yaml
```

From a checkout:

```bash
poetry run boomerang-alert-engine \
  --config stack/common.services.yaml \
  --config stack/alert_engine.yaml
```
