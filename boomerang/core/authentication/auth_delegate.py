from __future__ import annotations

import logging
from datetime import datetime, timezone

from kontiki.configuration.parameter import get_parameter
from kontiki.delegate import ServiceDelegate

from boomerang.core.service_contracts.identity.service import IdentityRpcProxy
from boomerang.core.exceptions import AuthError


def _parse_utc_timestamp(value: str) -> datetime:
    return datetime.fromisoformat(value.replace("Z", "+00:00"))


class AuthSessionDelegate(ServiceDelegate):
    def __init__(self, messenger):
        super().__init__()
        self._messenger = messenger
        self._is_configured = False
        self._max_cache_entries = 2048
        self._session_cache: dict[str, tuple[dict, datetime]] = {}

    async def setup(self) -> None:
        config = self.container.config
        self._max_cache_entries = int(
            get_parameter(config, "app.auth.session_cache.max_entries", 2048)
        )
        self._is_configured = True

    async def ensure_setup(self) -> None:
        if self._is_configured:
            return
        await self.setup()

    @staticmethod
    def _extract_bearer_token(auth_header) -> str:
        if not isinstance(auth_header, str):
            logging.warning("Invalid authentication header: %s", auth_header)
            raise AuthError()
        scheme, _, token = auth_header.partition(" ")
        if scheme.lower() != "bearer" or not token.strip():
            logging.warning("Invalid authentication header: %s", auth_header)
            raise AuthError()
        return token.strip()

    @staticmethod
    def _cache_deadline_from_session(session: dict) -> datetime | None:
        cache_valid_until = session.get("cache_valid_until")
        if isinstance(cache_valid_until, str) and cache_valid_until.strip():
            return _parse_utc_timestamp(cache_valid_until)
        session_expires_at = session.get("session_expires_at")
        if isinstance(session_expires_at, str) and session_expires_at.strip():
            return _parse_utc_timestamp(session_expires_at)
        return None

    def _prune_if_needed(self) -> None:
        while len(self._session_cache) > self._max_cache_entries:
            self._session_cache.pop(next(iter(self._session_cache)))

    async def require_authenticated_session(self, auth_header):
        await self.ensure_setup()
        access_token = self._extract_bearer_token(auth_header)
        now = datetime.now(timezone.utc)

        cached = self._session_cache.get(access_token)
        if cached is not None:
            session, valid_until = cached
            if now < valid_until:
                return session
            self._session_cache.pop(access_token, None)

        rpc_client = IdentityRpcProxy(self._messenger)
        try:
            session = await rpc_client.verify_session(access_token)
        except Exception as exc:
            logging.warning("Failed to verify session: %s", exc)
            raise AuthError() from exc

        if not isinstance(session, dict):
            logging.warning("Invalid session: %s", session)
            raise AuthError()
        if not isinstance(session.get("user_id"), str) or not isinstance(
            session.get("email"), str
        ):
            logging.warning("Invalid session: %s", session)
            raise AuthError()

        valid_until = self._cache_deadline_from_session(session)
        if valid_until is not None and now < valid_until:
            self._session_cache[access_token] = (session, valid_until)
            self._prune_if_needed()

        return session
