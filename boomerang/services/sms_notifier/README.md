# SMS Notifier Service

`sms-notifier-service` is the Boomerang service responsible for:

- managing authenticated user SMS endpoints over HTTP,
- consuming `sms.alerting.notification.requested` events,
- sending SMS through an HTTP provider endpoint,
- publishing delivery outcomes (`delivered` / `failed`).

## Implemented HTTP endpoints

All endpoints below are authenticated through `identity-service` (`@requires_identity_auth`).

- `POST /sms/endpoints`  
  Create or update one SMS endpoint for the authenticated user.
- `GET /sms/endpoints`  
  List SMS endpoints for the authenticated user.
- `GET /sms/endpoints/{endpoint_key}`  
  Get one SMS endpoint by key.
- `DELETE /sms/endpoints/{endpoint_key}`  
  Delete one SMS endpoint by key.

Storage uses SQLite and table `sms_endpoints` keyed by `(user_id, endpoint_key)`.

## Implemented event flow

Consumes:

- `sms.alerting.notification.requested`

Behavior:

- parse payload as `NotificationRequest` (`boomerang_contracts.notification`),
- resolve the destination phone via SQLite using `(recipient_id, endpoint_key)`,
- send HTTP request to provider `POST {app.sms.provider.base_url}/sms/send`,
- publish:
  - `alerting.notification.delivered` on success,
  - `alerting.notification.failed` (`delivery_error`) on failure.

## SMS provider configuration

Current implementation reads:

- `app.sms.provider.base_url`
- `app.sms.provider.api_key`
- `app.sms.provider.sender_id`

Request payload sent to provider:

- `to`
- `body`
- `sender_id`
- `title`

## Integration tests

Current integration coverage includes:

- create/update endpoint (`create-sms-endpoint.feature`),
- list/get/delete endpoints (`manage-sms-endpoints.feature`),
- consume delivery request + outcome publication (`consume-notification-requested.feature`).

For event-driven tests, provider-side HTTP calls are captured using a Kontiki `MockService`
with an HTTP entrypoint (`/sms/send`) and `MockServiceManager.get_http_requests(...)`.
