# Identity Service

`identity-service` centralizes user authentication and session issuance for the
other Boomerang services.

## What it does

- Accept auth code requests.
- Validate and consume auth codes.
- Issue auth/session tokens.
- Expose session verification through RPC (`verify_session`).
- Publish outbound auth-related events produced by delegate outcomes.

## Implemented HTTP endpoints

- `POST /auth/request-auth-code`  
  Start login flow (request an authentication code).
- `POST /auth/consume-auth-code`  
  Consume code and create an authenticated session.

Error mapping includes:

- `422` invalid payload,
- `401` auth failure,
- `429` rate limit.

## Implemented RPC API

- `verify_session(access_token: str)`  
  Used by business services (for example `subscription-service`, notifier HTTP
  endpoints) to validate bearer tokens.

## Architecture notes

- HTTP handlers delegate business logic to `IdentityDelegate`.
- Delegate outcomes may include outbound events; service publishes them through
  `Messenger`.
- Persistence is SQLite in MVP (`boomerang/services/identity/database`).

## Service boundaries

This service does **not**:

- manage subscriptions,
- resolve alert recipients,
- deliver channel notifications.
