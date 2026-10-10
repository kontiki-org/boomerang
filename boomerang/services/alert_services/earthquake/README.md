# Earthquake feed

The earthquake feed polls the USGS GeoJSON feed and publishes a `NormalizedAlert` for each new quake. `make stack-up-demo` runs it with the rest of the stack.

## Configure and run

`app.earthquake.min_magnitude` drops smaller events. `app.earthquake.usgs.feed_url` is the feed. Published alerts use `app.earthquake.category`. Field reference: [configuration](../../../../docs/configuration.md#earthquake-feed-service-demo-producer).

```yaml
app:
  earthquake:
    usgs:
      feed_url: "https://earthquake.usgs.gov/earthquakes/feed/v1.0/summary/1.0_hour.geojson"
    min_magnitude: 2
    category: natural.earthquake
```

RabbitMQ and the registry come from `stack/common.services.yaml`. The demo subscription is `stack/subscription.demo.yaml`.

```bash
docker run --rm \
  -v "$PWD/stack:/stack:ro" \
  ghcr.io/kontiki-org/boomerang-earthquake-feed:1.0.0 \
  --config /stack/common.services.yaml \
  --config /stack/earthquake.yaml
```

From a checkout:

```bash
poetry run boomerang-earthquake-feed \
  --config stack/common.services.yaml \
  --config stack/earthquake.yaml
```
