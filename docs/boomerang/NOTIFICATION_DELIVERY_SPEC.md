# Notification Delivery Specification (v1)

> **Status**: partially archived. The implementation note at the top is still useful,
> but this spec also contains older request-shape examples.  
> **Canonical docs**:
> - `docs/boomerang/EXISTING.md` (what exists today)
> - `docs/boomerang/ROADMAP.md` (enhancements / roadmap)
> - `boomerang/core/contracts/alert_normalized.py` (canonical normalized alert contract, phase 1)

## Goal

Define a channel-agnostic output contract so Boomerang can deliver alerts through
multiple targets (email, SMS, Slack, Zulip, webhook, push) without changing core alert logic.

This spec standardizes:
- request events emitted toward channel providers,
- outcome events emitted by channel provider services.

---

## Implementation note (this repository)

`alert-engine-service` publishes **channel-scoped** request topics:

- `email.alerting.notification.requested`
- `sms.alerting.notification.requested`
- (pattern: `{channel}.alerting.notification.requested`)

Payload is the Pydantic model **`NotificationRequest`** in
`boomerang/core/contracts/notification.py`:

- `channel`, `recipient_id`, `endpoint_key`
- `message`: `title`, `body`, `context` (`NotificationContext`: `kind`, `data`)

Channel notifiers load the concrete address/phone from storage using
`(recipient_id, endpoint_key)` instead of embedding a `destination` on the event.

The JSON example below documents an **earlier generic** `alerting.notification.requested`
shape; outcomes (`alerting.notification.delivered` / `failed`) still match the
outcome sections of this document.

---

## Event model

All events use a CloudEvents-style envelope.

### Delivery request event

`type: alerting.notification.requested`

```json
{
  "specversion": "1.0",
  "id": "evt_req_01",
  "type": "alerting.notification.requested",
  "source": "boomerang/alert-dispatch",
  "subject": "delivery_01",
  "time": "2026-03-26T20:20:00Z",
  "datacontenttype": "application/json",
  "data": {
    "delivery_id": "delivery_01",
    "alert_id": "alert_456",
    "recipient_id": "user_42",
    "channel": "slack",
    "destination": {
      "kind": "slack_channel",
      "value": "#weather-alerts"
    },
    "message": {
      "title": "Severe thunderstorm warning",
      "body": "Thunderstorms expected tonight in your area.",
      "severity": "severe",
      "language": "en"
    },
    "context": {
      "category": "weather",
      "zone_code": "FR-69",
      "correlation_id": "corr_123"
    },
    "dedup_key": "alert_456:user_42:slack",
    "requested_at": "2026-03-26T20:20:00Z",
    "attempt": 1
  }
}
```

### Delivery outcome events

`type: alerting.notification.delivered`  
`type: alerting.notification.failed`

```json
{
  "specversion": "1.0",
  "id": "evt_out_01",
  "type": "alerting.notification.delivered",
  "source": "boomerang/slack-provider",
  "subject": "delivery_01",
  "time": "2026-03-26T20:20:03Z",
  "datacontenttype": "application/json",
  "data": {
    "delivery_id": "delivery_01",
    "alert_id": "alert_456",
    "recipient_id": "user_42",
    "channel": "slack",
    "status": "delivered",
    "provider_message_id": "msg_abc123",
    "attempt": 1,
    "delivered_at": "2026-03-26T20:20:03Z",
    "error": null
  }
}
```

For failures:
- `status = "failed"`
- `error` contains a normalized error object.

---

## Required fields

### Request `data`
- `delivery_id`
- `alert_id`
- `recipient_id`
- `channel`
- `destination`
- `message`
- `requested_at`
- `attempt`

### Outcome `data`
- `delivery_id`
- `alert_id`
- `recipient_id`
- `channel`
- `status`
- `attempt`

---

## Standard channels

- `email`
- `sms`
- `slack`
- `zulip`
- `webhook`
- `push`

Providers can support a subset.

---

## Destination object

```json
{
  "kind": "email_address | phone_number | slack_channel | zulip_stream | webhook_url | push_token",
  "value": "channel specific destination"
}
```

`destination.kind` is mandatory and determines provider routing/validation.

---

## Routing and extension rule

- Request publication may come from `alert-engine-service` (per-channel topics in this repo)
  or from a dedicated `alert-dispatch-service` (generic `alerting.notification.requested` topic).
- Channel providers subscribe to their topic (or filter on `channel` when using a single bus).
- Adding a new target requires a new provider service and endpoint resolution rules.

---

## Backward compatibility

If legacy events are already used (`notification.email.requested`, `alert.delivered`, `alert.failed`),
they should be treated as transitional aliases. New integrations should use this spec.

