# Alert engine

The alert engine accepts a `NormalizedAlert` from the bus (`alert.normalized`) or from `POST /alerts`, asks subscription for the recipients, and publishes one `NotificationRequest` per endpoint.

Recipients are resolved via RPC to `subscription-service`. Framework options (`kontiki.*`) are documented with Kontiki.

## `app.http`

| Key | Default | Description |
|-----|---------|-------------|
| `app.http.token` | `""` | Bearer token for `POST /alerts`. Empty means HTTP ingest rejects as unauthorized. |

`POST /alerts` (status `202`) expects `Authorization: Bearer <app.http.token>` and a JSON `NormalizedAlert` body. It follows the same path as the bus event. HTTP listens on port 8005.

```yaml
app:
  http:
    token: "change-me"
```

RabbitMQ and the registry come from `stack/common.services.yaml`.

## Install

```bash
pip install boomerang-alert-engine==1.0.0
```

The package version is the image tag. After install the command is `boomerang-alert-engine`.

## Run

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
