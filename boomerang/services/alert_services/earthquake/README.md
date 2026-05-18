# Earthquake feed service

`earthquake-feed-service` polls the **USGS** public GeoJSON earthquake feed and
publishes **`alert.normalized`** events (`NormalizedAlert`) for the rest of the
Boomerang pipeline.

It also exposes RPC **`get_alert_subscription_catalog`**, returning
`AlertConnectorCatalog` for subscription UI and aggregation by `subscription-service`.

See **`docs/boomerang/EARTHQUAKE_SERVICE_ARCHITECTURE.md`** for architecture,
configuration, and USGS usage notes.

## Run

```bash
poetry run boomerang-earthquake-feed --config /path/to/config.yaml
```

Minimal `config.yaml` needs Kontiki AMQP settings plus optional `app.earthquake.*`
keys (defaults exist for URL, magnitude threshold, and demo `subscription_area`).

## Subscription area vs geolocation (MVP)

Today **`app.earthquake.subscription_area`** (`type` + `value`) is **operator
configuration**, not derived from USGS coordinates. Every normalized alert uses
that single **`areas[0]`** so the **subscription store** can match the same
`(area_type, area_value)` as in user subscriptions. In practice you can align
subscriptions with one logical “bucket” and receive **all qualifying events from
the configured feed** (still subject to feed scope, **`min_magnitude`**, category
allowlists, and dedupe)—not true geographic targeting yet.

**If you want real zones** you need a **geo matching layer** somewhere in the
pipeline, for example:

- **In this connector** before `publish`: enrich or replace `areas` only when the
  event intersects known geometries (heavier connector, geo data ownership here).
- **In the core** (`alert-engine` + **`subscription-service`** / RPC): keep a rich
  payload (coordinates, region codes, …) and resolve recipients with **spatial
  queries** or a table **`subscription_area → geometry`** (often preferable so all
  alert sources share one model).
- **Dedicated normalization / geozone service** between source and engine, similar
  to splitting ingestion and normalization for other domains.

Filtering usually happens **when going from alert to subscribers** (or before
publish if you only want geo-scoped events on the bus), not at SMS/email send time:
by then recipients are already chosen.

## Integration tests (Behave)

With RabbitMQ running (e.g. `make run-amqp`):

```bash
make integration-test-earthquake-feed
```
