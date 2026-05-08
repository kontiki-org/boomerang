# Boomerang — Existing system (source of truth)

This document describes **what is implemented today** in this repository.

If you are looking for future plans, see **`docs/boomerang/ROADMAP.md`**.

---

## Scope

Boomerang is a **self-hostable alerting pipeline** built around:

- upstream **domain connectors** that publish **`alert.normalized`**
- a core **alert engine** that resolves recipients via RPC and emits **channel-scoped notification requests**
- downstream **channel notifiers** that deliver and publish **delivery outcomes**
- user-facing APIs currently available over **HTTP and RPC (AMQP)**, with near-term UI integration focused on RPC/AMQP

---

## Implemented macro architecture

```text
<domain connector> (example: earthquake-feed-service)
  -> alert.normalized
  -> alert-engine-service
  --RPC--> subscription-service.get_recipients_for_alert(...)
  -> {channel}.alerting.notification.requested
  -> email-notifier-service / sms-notifier-service
  -> alerting.notification.delivered | alerting.notification.failed
```

### Core services (as implemented)

- **`earthquake-feed-service`** (domain connector)
  - polls USGS GeoJSON
  - publishes `alert.normalized`
- **`alert-engine-service`**
  - consumes `alert.normalized`s
  - calls `subscription-service.get_recipients_for_alert(...)` (RPC)
  - publishes `{channel}.alerting.notification.requested`
- **`subscription-service`**
  - stores subscriptions and channel attachment metadata (SQLite in MVP)
  - provides recipient resolution via RPC
  - exposes HTTP CRUD for subscriptions (behind identity verification)
  - exposes RPC for recipient resolution and channel attachment (`attach_channel_endpoint`)
- **`identity-service`**
  - user-facing auth-code flow (HTTP)
  - provides RPC `verify_session` for downstream services
- **`email-notifier-service` / `sms-notifier-service`**
  - consume `email.alerting.notification.requested` / `sms.alerting.notification.requested`
  - resolve destination from endpoint storage using `(recipient_id, endpoint_key)`
  - publish outcomes: `alerting.notification.delivered` / `alerting.notification.failed`
  - `email-notifier-service` also exposes a degraded heartbeat state via `@degraded_on` when SMTP delivery failures accumulate

### Optional / not on hot path

- **`alert-dispatch-service`** is documented but **not** used on the hot path in the current repository. Fan-out happens in `alert-engine-service`.

---

## Contracts (events)

### Normalized alert input

- **Topic**: `alert.normalized`
- **Owner**: upstream normalizers/connectors
- **Consumed by**: `alert-engine-service`

Minimum fields expected by the engine include:
`alert_id`, `category`, `event_type`, `severity`, `areas`, `headline`, `message`,
`effective_at`, `expires_at` (exact shape may evolve; see service README(s) for
the canonical contract used by the engine).

Phase 1 contract clarification introduces a canonical model for normalized alerts:
`boomerang.core.contracts.alert_normalized.NormalizedAlert` (`schema_version=1.0`),
with an extensible `attributes` map for producer-specific data.

### Notification request (per channel)

- **Topic pattern**: `{channel}.alerting.notification.requested`
  - examples: `email.alerting.notification.requested`, `sms.alerting.notification.requested`
- **Payload model (implementation)**: `boomerang.core.contracts.notification.NotificationRequest`
  - includes `channel`, `recipient_id`, `endpoint_key`, and a `message` object

Phase 1 contract clarification also defines target subscription contracts:
- generic criteria (`key`, `operator`, `value`) through
  `boomerang.core.contracts.subscription.CriteriaExpression`
- direct destination binding at subscription level through
  `boomerang.core.contracts.subscription.EndpointRef`

### Delivery outcomes

- **Topics**:
  - `alerting.notification.delivered`
  - `alerting.notification.failed`
- **Emitted by**: channel notifier services

> Note: `docs/boomerang/NOTIFICATION_DELIVERY_SPEC.md` contains historical examples
> that describe an earlier generic request event (`alerting.notification.requested`)
> embedding a `destination`. The repository implementation uses channel-scoped
> request topics and resolves destination from endpoint storage.

---

## Contracts (HTTP and RPC)

This repository currently exposes user-facing HTTP for:

- identity: auth-code flow and session issuance
- subscriptions: create/list/update/pause/delete
- endpoints: manage email/SMS endpoints

This repository also exposes AMQP RPC for service-to-service interactions and UI client integration:

- identity: `request_auth_code`, `consume_auth_code`, `verify_session`
- subscription: recipient resolution and channel attachment, plus authenticated subscription operations
- email-notifier: endpoint management and `ensure_auth_email_endpoint`

Authorization for authenticated service calls is enforced by downstream services calling `identity-service.verify_session` (RPC).

---

## Where to look for “truth”

- **Service runtime behavior**: service-level README(s) under `boomerang/services/**/README.md`
- **Delivery contract notes**: `docs/boomerang/NOTIFICATION_DELIVERY_SPEC.md` (implementation notes at the top are most relevant)
