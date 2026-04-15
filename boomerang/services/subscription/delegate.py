import logging
import re
import secrets
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
    RateLimitError,
    ValidationError,
)
from boomerang.services.subscription.outcome import EntrypointOutcome, OutboundEvent

EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
CODE_RE = re.compile(r"^\d{6}$")


class SubscriptionDelegate(ServiceDelegate):
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
        logging.info(
            "SubscriptionDelegate configured (ttl=%ss cooldown=%ss max_requests=%s window=%ss event=%s)",
            self._ttl_seconds,
            self._cooldown_seconds,
            self._rate_limit_max_requests,
            self._rate_limit_window_seconds,
            self._notification_event_type,
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

    async def create_subscription(self, request):
        raise NotImplementedError

    async def list_subscriptions(self, request):
        email = self._require_authenticated_email(request)
        logging.info("list_subscriptions for email=%s", email)
        return {"items": []}

    async def update_subscription(self, request):
        raise NotImplementedError

    async def delete_subscription(self, request):
        raise NotImplementedError

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
