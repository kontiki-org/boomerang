# Email Notifier Service

`email-notifier-service` manages user email endpoints and executes email delivery
for email channel notification requests.

## What it does

- Manage authenticated user email endpoints over HTTP.
- Consume `email.alerting.notification.requested`.
- Resolve destination using `(recipient_id, endpoint_key)` in local storage.
- Send email through configured SMTP/provider integration.
- Publish delivery outcomes:
  - `alerting.notification.delivered`
  - `alerting.notification.failed`

## Implemented HTTP endpoints

All endpoints below are authenticated through `identity-service` (`@requires_identity_auth`).

- `POST /email/endpoints`  
  Create or update one email endpoint for the authenticated user.
- `GET /email/endpoints`  
  List email endpoints for the authenticated user.
- `GET /email/endpoints/{endpoint_key}`  
  Get one email endpoint by key.
- `DELETE /email/endpoints/{endpoint_key}`  
  Delete one email endpoint by key.

Storage uses SQLite table `email_endpoints` keyed by `(user_id, endpoint_key)`.

## Implemented event flow

Consumes:

- `email.alerting.notification.requested`

Behavior:

- parse payload as `NotificationRequest`,
- load email endpoint from `(recipient_id, endpoint_key)`,
- send notification email through delegate/provider client,
- publish:
  - `alerting.notification.delivered` on success,
  - `alerting.notification.failed` (`delivery_error`) on failure.

## Service boundaries

This service does **not**:

- compute recipients,
- decide channels,
- produce domain alerts.
