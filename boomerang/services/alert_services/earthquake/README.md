# Earthquake feed service

`earthquake-feed-service` polls the **USGS** public GeoJSON earthquake feed and
publishes **`alert.normalized`** events for the rest of the Boomerang pipeline.

See **`docs/boomerang/EARTHQUAKE_SERVICE_ARCHITECTURE.md`** for architecture,
configuration, and USGS usage notes.

## Run

```bash
poetry run boomerang-earthquake-feed --config /path/to/config.yaml
```

Minimal `config.yaml` needs Kontiki AMQP settings plus optional `app.earthquake.*`
keys (defaults exist for URL, magnitude threshold, and demo `subscription_area`).
