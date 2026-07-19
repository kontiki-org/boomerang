# Subscription Service

`subscription-service` stores subscription preferences and resolves recipients for alerts.

It is domain-agnostic: it does not produce alerts and it does not send
notifications.

## What it does

- Load subscriptions from YAML (`app.subscriptions`).
- Aggregate alert subscription catalogs from configured connectors
  (`GET /alert-catalog`, RPC `get_alert_subscription_catalog`).
- Aggregate notification channel catalogs from configured notifiers
  (`GET /notification-channels/catalog`, RPC `get_notification_channels_catalog`).
- Provide recipient targeting through RPC (`get_recipients_for_alert`).

## Stack

- Config: `stack/subscription.yaml` (demo overlay: `stack/subscription.demo.yaml`)
- HTTP (catalogues): port **8002** → http://127.0.0.1:8002/api/v1/docs
- Connectors: `app.alert_connectors`
- Notifiers: `app.notification_channels`

YAML is the primary way to declare subscriptions and attach channel endpoints for
local / embedded runs. There is no interactive auth CRUD HTTP surface on this
service.

## Architecture notes

- Subscriptions are declared in YAML (`app.subscriptions`).
- Alert connectors are listed in `app.alert_connectors` (RPC fan-out to each
  connector’s `get_alert_subscription_catalog`).
- Notification notifiers are listed in `app.notification_channels` (RPC fan-out
  to each notifier’s `get_notification_channel_catalog`).
- Allowed channel IDs (`email`, `telegram`, …) come from the aggregated
  notification channel catalog.
- Channel endpoint credentials are not stored here; notifier services own
  endpoint storage and delivery.
- Recipient matching currently uses **`areas[0]`** only (single-area MVP).

## Service boundaries

This service does **not**:

- ingest domain events,
- evaluate alert generation rules,
- send notifications directly.
