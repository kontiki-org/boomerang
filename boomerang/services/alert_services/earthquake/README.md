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
category, TTL, and HTTP timeout.

Demo overlay registers the connector on subscription via
`stack/subscription.demo.yaml` (`app.alert_connectors`).

## Subscription matching (demo)

Alerts ship with **empty `areas`**. Demo subscriptions typically match
`category` / `event_type` (catch-all criteria) and optionally **`magnitude`**
(`gte`). Feed-level filtering uses **`min_magnitude`**.

True geographic targeting (USGS coordinates → zones) is future work: enrich
alerts or match at subscription time — not at notifier delivery.

## Integration tests (Behave)

With the local platform running (e.g. `make run-dev-platform`):

```bash
make integration-test-earthquake-feed
```
