# Subscription Service

`subscription-service` is the Boomerang service that stores user subscription
preferences for alerts.

It is domain-agnostic: it does not produce alerts and it does not send
notifications. Its job is to keep subscription data consistent and expose it to
the rest of the platform.

## What it does

- Manage authenticated user subscriptions (create, get, update, delete).
- Aggregate alert subscription catalogs from configured connectors
  (`GET /alert-catalog`, RPC `get_alert_subscription_catalog`).
- Aggregate notification channel catalogs from configured notifiers
  (`GET /notification-channels/catalog`, RPC `get_notification_channels_catalog`).
- Proxy endpoint CRUD to configured notification channels (RPC + HTTP).
- Provide recipient targeting through RPC (`get_recipients_for_alert`).

## Architecture notes

- Authentication is delegated to `identity-service`.
  - This service validates bearer tokens via identity RPC.
- Storage is SQLite for MVP.
- Alert connectors are listed in `app.alert_connectors` (RPC fan-out to each
  connector’s `get_alert_subscription_catalog`).
- Notification notifiers are listed in `app.notification_channels` (RPC fan-out
  to each notifier’s `get_notification_channel_catalog` and endpoint CRUD).
- Allowed channel IDs (`email`, `telegram`, …) come from the aggregated
  notification channel catalog, not from a separate config list.
- Channel endpoint credentials are not stored here; notifier services own
  endpoint storage and delivery.

## Service boundaries

This service does **not**:

- ingest domain events,
- evaluate alert generation rules,
- send notifications directly.
