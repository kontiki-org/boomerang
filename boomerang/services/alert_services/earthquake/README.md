# Earthquake feed service

`earthquake-feed-service` polls the **USGS** public GeoJSON earthquake feed and
publishes **`alert.normalized`** events (`NormalizedAlert`) for the rest of the
Boomerang pipeline.

It also exposes RPC **`get_alert_subscription_catalog`**, returning an
`AlertConnectorCatalog` for aggregation by `subscription-service`.

This is the optional **demo** producer (`make stack-up-demo`), not part of the
core alerting runtime.

## Run

Stack (with core):

```bash
make stack-up-demo
```

Standalone:

```bash
poetry run boomerang-earthquake-feed --config /path/to/config.yaml
```

Example config: `stack/earthquake.yaml` (merged with `stack/common.services.yaml`
in Compose). Keys under `app.earthquake.*` cover feed URL, `min_magnitude`,
`subscription_area`, category, TTL, and HTTP timeout.

Demo overlay registers the connector on subscription via
`stack/subscription.demo.yaml` (`app.alert_connectors`).

## Subscription area vs geolocation (MVP)

Today **`app.earthquake.subscription_area`** (`type` + `value`) is **operator
configuration**, not derived from USGS coordinates. Every normalized alert uses
that single **`areas[0]`** so **YAML subscriptions** can match the same
`(area_type, area_value)`. In practice you can align
subscriptions with one logical “bucket” and receive **all qualifying events from
the configured feed** (still subject to feed scope, **`min_magnitude`**, and
dedupe)—not true geographic targeting yet.

**If you want real zones**, add a geo matching layer somewhere in the pipeline
(connector enrichment, core spatial matching, or a dedicated geozone service).
Filtering belongs when resolving subscribers (or before publish), not at notifier
delivery time.

## Integration tests (Behave)

With the local platform running (e.g. `make run-dev-platform`):

```bash
make integration-test-earthquake-feed
```
