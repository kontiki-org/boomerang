import logging
import re
import secrets
from functools import wraps
from datetime import datetime, timedelta, timezone

from kontiki.configuration.parameter import get_parameter
from kontiki.delegate import ServiceDelegate

from boomerang.core.contracts.notification import (
    NotificationContext,
    NotificationDestination,
    NotificationMessage,
    NotificationRequest,
)
from boomerang.services.subscription.exceptions import (
    AuthError,
    NotFoundError,
    RateLimitError,
    ValidationError,
)
from boomerang.services.subscription.database import Database
from boomerang.services.subscription.http_models import (
    CreateSubscriptionRequest,
    UpdateSubscriptionRequest,
)
from boomerang.services.subscription.outcome import EntrypointOutcome, OutboundEvent

EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
CODE_RE = re.compile(r"^\d{6}$")


class SubscriptionDelegate(ServiceDelegate):
    @staticmethod
    def requires_auth(handler):
        @wraps(handler)
        async def wrapper(self, request, *args, **kwargs):
            email = self._require_authenticated_email(request)
            return await handler(self, request, *args, email=email, **kwargs)

        return wrapper

    async def setup(self):
        self._tokens = {}
        self._access_tokens = {}
        self._request_timestamps = {}
        self._last_request_at = {}

        self._ttl_seconds = int(
            get_parameter(self.container.config, "app.auth.auth_code.ttl_seconds", 600)
        )
        self._cooldown_seconds = int(
            get_parameter(
                self.container.config,
                "app.auth.auth_code.cooldown_seconds",
                30,
            )
        )
        self._rate_limit_max_requests = int(
            get_parameter(
                self.container.config,
                "app.auth.auth_code.rate_limit.max_requests",
                3,
            )
        )
        self._rate_limit_window_seconds = int(
            get_parameter(
                self.container.config,
                "app.auth.auth_code.rate_limit.window_seconds",
                600,
            )
        )
        self._notification_event_type = get_parameter(
            self.container.config,
            "app.auth.auth_code.notification_event_type",
            "alerting.notification.requested",
        )
        self._storage_backend = get_parameter(
            self.container.config,
            "app.storage.backend",
            "sqlite",
        )
        self._sqlite_path = get_parameter(
            self.container.config,
            "app.storage.sqlite_path",
            "/data/subscriptions.db",
        )
        if self._storage_backend != "sqlite":
            raise RuntimeError("Unsupported storage backend for MVP.")
        self._database = Database(self._sqlite_path)
        self._database.setup()
        logging.info(
            "SubscriptionDelegate configured (ttl=%ss cooldown=%ss max_requests=%s window=%ss event=%s backend=%s path=%s)",
            self._ttl_seconds,
            self._cooldown_seconds,
            self._rate_limit_max_requests,
            self._rate_limit_window_seconds,
            self._notification_event_type,
            self._storage_backend,
            self._sqlite_path,
        )

    async def _parse_request_email(self, request):
        try:
            body = await request.json()
        except Exception as exc:
            raise ValidationError("Invalid request payload.") from exc

        email = body.get("email")
        if not isinstance(email, str):
            raise ValidationError("Invalid request payload.")

        email = email.strip().lower()
        if not email or not EMAIL_RE.match(email):
            raise ValidationError("Invalid request payload.")

        return email

    def _enforce_rate_limits(self, email, now):
        last_request = self._last_request_at.get(email)
        if (
            self._cooldown_seconds > 0
            and last_request is not None
            and (now - last_request).total_seconds() < self._cooldown_seconds
        ):
            raise RateLimitError("Too many requests. Please try again later.")

        window_start = now - timedelta(seconds=self._rate_limit_window_seconds)
        timestamps = self._request_timestamps.get(email, [])
        timestamps = [ts for ts in timestamps if ts >= window_start]
        if len(timestamps) >= self._rate_limit_max_requests:
            self._request_timestamps[email] = timestamps
            raise RateLimitError("Too many requests. Please try again later.")

        timestamps.append(now)
        self._request_timestamps[email] = timestamps
        self._last_request_at[email] = now

    def _generate_auth_code(self):
        return f"{secrets.randbelow(1000000):06d}"

    def _extract_bearer_token(self, request):
        auth_header = request.headers.get("Authorization", "")
        if not isinstance(auth_header, str):
            raise AuthError("Authentication required or invalid.")
        scheme, _, token = auth_header.partition(" ")
        if scheme.lower() != "bearer" or not token.strip():
            raise AuthError("Authentication required or invalid.")
        return token.strip()

    def _require_authenticated_email(self, request):
        access_token = self._extract_bearer_token(request)
        session = self._access_tokens.get(access_token)
        if not isinstance(session, dict):
            raise AuthError("Authentication required or invalid.")
        email = session.get("email")
        if not isinstance(email, str) or not email:
            raise AuthError("Authentication required or invalid.")
        return email

    async def get_recipients_for_zone(self, zone_code, severity, category):
        raise NotImplementedError

    async def request_auth_code(self, request):
        email = await self._parse_request_email(request)
        now = datetime.now(timezone.utc)
        logging.info("request_auth_code received for email=%s", email)
        self._enforce_rate_limits(email, now)

        auth_code = self._generate_auth_code()
        expires_at = now + timedelta(seconds=self._ttl_seconds)
        self._tokens[auth_code] = {
            "email": email,
            "expires_at": expires_at,
            "used": False,
        }
        logging.info("auth code created for email=%s expires_at=%s", email, expires_at)

        message = NotificationRequest(
            channel="email",
            destination=NotificationDestination(
                kind="email_address",
                value=email,
            ),
            message=NotificationMessage(
                title="Boomerang sign in",
                body="Use this verification code to sign in.",
                context=NotificationContext(
                    kind="auth.code",
                    data={
                        "auth_code": auth_code,
                        "expires_at": expires_at.isoformat().replace("+00:00", "Z"),
                    },
                ),
            ),
        )

        return EntrypointOutcome(
            http_response={"status": "ok"},
            events=[
                OutboundEvent(
                    event_type=self._notification_event_type,
                    payload=message,
                )
            ],
        )

    async def consume_auth_code(self, request):
        try:
            body = await request.json()
        except Exception as exc:
            raise ValidationError("Invalid request payload.") from exc

        auth_code = body.get("code")
        if not isinstance(auth_code, str) or not auth_code.strip():
            raise ValidationError("Invalid request payload.")
        auth_code = auth_code.strip()
        if not CODE_RE.match(auth_code):
            raise ValidationError("Invalid request payload.")

        record = self._tokens.get(auth_code)
        if record is None:
            raise AuthError("Authentication required or invalid.")

        now = datetime.now(timezone.utc)
        if record.get("used"):
            raise AuthError("Authentication required or invalid.")

        expires_at = record.get("expires_at")
        if not isinstance(expires_at, datetime) or now >= expires_at:
            raise AuthError("Authentication required or invalid.")

        record["used"] = True
        access_token = secrets.token_urlsafe(32)
        self._access_tokens[access_token] = {
            "email": record.get("email"),
            "created_at": now,
        }
        logging.info("auth code consumed for email=%s", record.get("email"))
        return EntrypointOutcome(
            http_response={
                "status": "ok",
                "access_token": access_token,
                "token_type": "Bearer",
            }
        )

    async def logout(self, request):
        raise NotImplementedError

    async def me(self, request):
        raise NotImplementedError

    @requires_auth
    async def create_subscription(self, request, body: CreateSubscriptionRequest, email):
        user_id = self._database.ensure_user(email)
        created, skipped, errors = self._database.create_subscriptions(user_id, body)

        logging.info(
            "create_subscription for email=%s created=%s skipped=%s errors=%s",
            email,
            len(created),
            len(skipped),
            len(errors),
        )
        return {"created": created, "skipped": skipped, "errors": errors}

    @requires_auth
    async def list_subscriptions(self, request, email):
        user_id = self._database.ensure_user(email)
        logging.info("list_subscriptions for email=%s", email)
        items = self._database.list_subscriptions(user_id)
        return {"items": items}

    @requires_auth
    async def update_subscription(
        self,
        request,
        subscription_id,
        body: UpdateSubscriptionRequest,
        email,
    ):
        user_id = self._database.ensure_user(email)
        updated = self._database.update_subscription(
            user_id=user_id,
            subscription_id=subscription_id,
            min_severity=body.min_severity,
            policy=body.policy.model_dump() if body.policy is not None else None,
            status=body.status,
        )
        if updated is None:
            raise NotFoundError("Resource not found.")
        return {"status": "ok", "item": updated}

    @requires_auth
    async def delete_subscription(self, request, subscription_id, email):
        user_id = self._database.ensure_user(email)
        deleted = self._database.delete_subscription(user_id, subscription_id)
        if not deleted:
            raise NotFoundError("Resource not found.")
        return {"status": "deleted"}

    async def upsert_channel(self, request):
        raise NotImplementedError

    async def list_channels(self, request):
        raise NotImplementedError

    async def update_channel(self, request):
        raise NotImplementedError

    async def delete_channel(self, request):
        raise NotImplementedError

    async def list_channel_catalog(self, request):
        raise NotImplementedError

    async def list_categories(self, request):
        raise NotImplementedError
