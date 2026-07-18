import logging
import re
import secrets
from datetime import datetime, timedelta, timezone

from kontiki.configuration.parameter import get_parameter
from kontiki.delegate import ServiceDelegate
from kontiki.messaging import Messenger

from boomerang.core.service_contracts.email_notifier.service import EmailNotifierRpcProxy
from boomerang_contracts.notification.message import (
    NotificationContext,
    NotificationMessage,
    NotificationRequest,
)
from boomerang.core.exceptions import AuthError, ValidationError
from boomerang.services.identity.database import Database
from boomerang.services.identity.exceptions import DependencyError, RateLimitError

EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
CODE_RE = re.compile(r"^\d{6}$")


class IdentityDelegate(ServiceDelegate):
    async def setup(self):
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
        self._session_cache_safety_margin_seconds = int(
            get_parameter(
                self.container.config,
                "app.auth.session_cache.safety_margin_seconds",
                10,
            )
        )
        self._notification_event_type = get_parameter(
            self.container.config,
            "app.auth.auth_code.notification_event_type",
            "email.alerting.notification.requested",
        )
        self._storage_backend = get_parameter(
            self.container.config,
            "app.storage.backend",
            "sqlite",
        )
        self._sqlite_path = get_parameter(
            self.container.config,
            "app.storage.sqlite_path",
            "/data/identity.db",
        )
        if self._storage_backend != "sqlite":
            raise RuntimeError("Unsupported storage backend for MVP.")

        self._database = Database(self._sqlite_path)
        self._database.setup()
        logging.info(
            "IdentityDelegate configured (ttl=%ss cooldown=%ss max_requests=%s window=%ss session_cache_margin=%ss event=%s backend=%s path=%s)",
            self._ttl_seconds,
            self._cooldown_seconds,
            self._rate_limit_max_requests,
            self._rate_limit_window_seconds,
            self._session_cache_safety_margin_seconds,
            self._notification_event_type,
            self._storage_backend,
            self._sqlite_path,
        )

    @staticmethod
    def _parse_utc_timestamp(value: str) -> datetime:
        return datetime.fromisoformat(value.replace("Z", "+00:00"))

    def _enforce_rate_limits(self, email: str, now: datetime) -> None:
        last_request = self._last_request_at.get(email)
        if (
            self._cooldown_seconds > 0
            and last_request is not None
            and (now - last_request).total_seconds() < self._cooldown_seconds
        ):
            raise RateLimitError()

        window_start = now - timedelta(seconds=self._rate_limit_window_seconds)
        timestamps = self._request_timestamps.get(email, [])
        timestamps = [ts for ts in timestamps if ts >= window_start]
        if len(timestamps) >= self._rate_limit_max_requests:
            self._request_timestamps[email] = timestamps
            raise RateLimitError()

        timestamps.append(now)
        self._request_timestamps[email] = timestamps
        self._last_request_at[email] = now

    @staticmethod
    def _generate_auth_code() -> str:
        return f"{secrets.randbelow(1000000):06d}"

    @staticmethod
    def _generate_access_token() -> str:
        return secrets.token_urlsafe(32)

    async def _ensure_auth_email_endpoint(
        self, messenger, user_id: str, email: str
    ) -> None:
        rpc_client = EmailNotifierRpcProxy(messenger)
        try:
            await rpc_client.ensure_auth_email_endpoint(
                user_id=user_id,
                endpoint_key="email_primary",
                address=email,
            )
        except Exception as exc:
            raise DependencyError() from exc

    async def request_auth_code(self, email: str, messenger: Messenger):
        email = email.strip().lower()
        if not EMAIL_RE.match(email):
            raise ValidationError()

        now = datetime.now(timezone.utc)
        self._enforce_rate_limits(email, now)
        self._database.cleanup_expired()

        auth_code = self._generate_auth_code()
        expires_at = now + timedelta(seconds=self._ttl_seconds)
        expires_iso = expires_at.isoformat().replace("+00:00", "Z")
        self._database.insert_auth_code(auth_code, email, expires_iso)

        message = NotificationRequest(
            channel="email",
            recipient_id=Database.build_user_id(email),
            endpoint_key="email_primary",
            message=NotificationMessage(
                title="Boomerang sign in",
                body=f"Use this verification code to sign in: {auth_code}.",
                context=NotificationContext(
                    kind="auth.code",
                    data={
                        "auth_code": auth_code,
                        "expires_at": expires_iso,
                    },
                ),
            ),
        )

        await self._ensure_auth_email_endpoint(messenger, message.recipient_id, email)
        logging.info(
            "request_auth_code: published event type=%s", self._notification_event_type
        )
        await messenger.publish(self._notification_event_type, message)
        return {}

    async def consume_auth_code(self, code: str):
        auth_code = code.strip()
        if not CODE_RE.match(auth_code):
            raise ValidationError()

        self._database.cleanup_expired()
        record = self._database.get_auth_code(auth_code)
        if not isinstance(record, dict):
            raise AuthError()
        if record.get("used"):
            raise AuthError()

        expires_at = record.get("expires_at")
        if not isinstance(expires_at, str):
            raise AuthError()
        email = record.get("email")
        if not isinstance(email, str) or not email:
            raise AuthError()

        # mark used before issuing a token
        self._database.mark_auth_code_used(auth_code)

        now = datetime.now(timezone.utc)
        access_token = self._generate_access_token()
        user_id = Database.build_user_id(email)
        session_expires_at = now + timedelta(seconds=self._ttl_seconds)
        session_expires_iso = session_expires_at.isoformat().replace("+00:00", "Z")
        self._database.insert_session(access_token, user_id, email, session_expires_iso)

        return {
            "access_token": access_token,
            "token_type": "Bearer",
        }

    async def verify_session(self, access_token: str):
        self._database.cleanup_expired()
        if not isinstance(access_token, str) or not access_token.strip():
            raise AuthError()

        session = self._database.get_session(access_token.strip())
        if not isinstance(session, dict):
            raise AuthError()
        session_expires_at = session.get("expires_at")
        if not isinstance(session_expires_at, str):
            raise AuthError()
        expires_at_dt = self._parse_utc_timestamp(session_expires_at)
        cache_valid_until = expires_at_dt - timedelta(
            seconds=max(0, self._session_cache_safety_margin_seconds)
        )

        return {
            "user_id": session["user_id"],
            "email": session["email"],
            "session_expires_at": session_expires_at,
            "cache_valid_until": cache_valid_until.isoformat().replace("+00:00", "Z"),
        }
