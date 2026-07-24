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

Demo overlay (`stack/subscription.demo.yaml`) registers the connector
(`app.alert_connectors`) and ships an active subscription:
`natural.earthquake` / `earthquake`, `magnitude >= 2`, endpoints
`telegram.alerts` and `email.inbox`.

## Subscription matching (demo)

Alerts ship with **empty `areas`**. The sample rule matches category /
event_type and **`magnitude` `gte` 2**. Feed-level filtering uses
`app.earthquake.min_magnitude` (stock: `2`).

True geographic targeting (USGS coordinates → zones) is future work: enrich
alerts or match at subscription time — not at notifier delivery.

## Integration tests (Behave)

With the local platform running (e.g. `make run-dev-platform`):

```bash
make integration-test-earthquake-feed
```
