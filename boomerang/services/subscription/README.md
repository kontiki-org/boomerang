# Subscription Service

`subscription-service` is the Boomerang service that stores user subscription
preferences for alerts.

It is domain-agnostic: it does not produce alerts and it does not send
notifications. Its job is to keep subscription data consistent and expose it to
the rest of the platform.

## What it does

- Manage authenticated user subscriptions (create, get, update, delete).
- Expose allowed channel types from config (`GET /channels`).
- Expose allowed alert types from config (`GET /alerts`).
- Register user channel endpoints through RPC (`attach_channel_endpoint`).
- Provide recipient targeting through RPC (`get_recipients_for_alert`).

## Architecture notes

- Authentication is delegated to `identity-service`.
  - This service validates bearer tokens via identity RPC.
- Storage is SQLite for MVP.
- Allowed channels and alerts are config-driven (`app.channels`,
  `app.alerts.allowed`).
- Channel endpoint credentials are not stored here; provider services own
  provider-side auth flows and secrets.

## Service boundaries

This service does **not**:

- ingest domain events,
- evaluate alert generation rules,
- send notifications directly.
