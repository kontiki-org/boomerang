from datetime import datetime, timedelta, timezone
import re
import secrets

from kontiki.configuration.parameter import get_parameter
from kontiki.delegate import ServiceDelegate

from boomerang.services.subscription.exceptions import RateLimitError, ValidationError
from boomerang.services.subscription.outcome import EntrypointOutcome, OutboundEvent


EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


class SubscriptionDelegate(ServiceDelegate):
    async def setup(self):
        self._tokens = {}
        self._request_timestamps = {}
        self._last_request_at = {}

        self._ttl_seconds = int(
            get_parameter(self.container.config, "app.auth.magic_link.ttl_seconds", 600)
        )
        self._cooldown_seconds = int(
            get_parameter(self.container.config, "app.auth.magic_link.cooldown_seconds", 30)
        )
        self._rate_limit_max_requests = int(
            get_parameter(
                self.container.config, "app.auth.magic_link.rate_limit.max_requests", 3
            )
        )
        self._rate_limit_window_seconds = int(
            get_parameter(
                self.container.config, "app.auth.magic_link.rate_limit.window_seconds", 600
            )
        )
        self._consume_base_url = get_parameter(
            self.container.config,
            "app.auth.magic_link.consume_url_base",
            "http://localhost:8000/auth/consume-magic-link",
        )
        self._notification_event_type = get_parameter(
            self.container.config,
            "app.auth.magic_link.notification_event_type",
            "alerting.notification.requested",
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

    def _build_magic_link_url(self, token):
        separator = "&" if "?" in self._consume_base_url else "?"
        return f"{self._consume_base_url}{separator}token={token}"


    async def get_recipients_for_zone(self, zone_code, severity, category):
        raise NotImplementedError

    async def request_magic_link(self, request):
        email = await self._parse_request_email(request)
        now = datetime.now(timezone.utc)
        self._enforce_rate_limits(email, now)

        token = secrets.token_urlsafe(24)
        expires_at = now + timedelta(seconds=self._ttl_seconds)
        self._tokens[token] = {
            "email": email,
            "expires_at": expires_at,
            "used": False,
        }

        message = {
            "channel": "email",
            "destination": {
                "kind": "email_address",
                "value": email,
            },
            "message": {
                "title": "Boomerang sign in",
                "body": "Use this link to sign in.",
                "context": {
                    "kind": "auth.magic_link",
                    "data": {
                        "magic_link_url": self._build_magic_link_url(token),
                        "expires_at": expires_at.isoformat().replace("+00:00", "Z"),
                    },
                },
            },
        }

        return EntrypointOutcome(
            http_response={"status": "ok"},
            events=[
                OutboundEvent(
                    event_type=self._notification_event_type,
                    payload=message,
                )
            ],
        )

    async def consume_magic_link(self, request):
        raise NotImplementedError

    async def logout(self, request):
        raise NotImplementedError

    async def me(self, request):
        raise NotImplementedError

    async def create_subscription(self, request):
        raise NotImplementedError

    async def list_subscriptions(self, request):
        raise NotImplementedError

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
