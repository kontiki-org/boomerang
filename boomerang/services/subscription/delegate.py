import logging

from kontiki.configuration.parameter import get_parameter
from kontiki.delegate import ServiceDelegate
from kontiki.messaging import rpc_error

from boomerang.services.subscription.database import Database
from boomerang.services.subscription.exceptions import NotFoundError
from boomerang.services.subscription.http_models import (
    CreateSubscriptionRequest,
    UpdateSubscriptionRequest,
)


class SubscriptionDelegate(ServiceDelegate):
    async def setup(self):
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
        configured_channels = get_parameter(self.container.config, "app.channels", [])
        self._configured_channels = (
            configured_channels if isinstance(configured_channels, list) else []
        )
        if self._storage_backend != "sqlite":
            raise RuntimeError("Unsupported storage backend for MVP.")
        self._database = Database(self._sqlite_path)
        self._database.setup()
        logging.info(
            "SubscriptionDelegate configured (backend=%s path=%s)",
            self._storage_backend,
            self._sqlite_path,
        )

    async def get_recipients_for_zone(self, zone_code, severity, category):
        raise NotImplementedError

    async def attach_channel_endpoint(
        self,
        user_id: str,
        channel: str,
        endpoint_key: str,
        is_default: bool = False,
    ):
        user_id = user_id.strip()
        normalized_channel = channel.strip().lower()
        endpoint_key = endpoint_key.strip()

        logging.info(
            "attach_channel_endpoint for user_id=%s channel=%s endpoint_key=%s is_default=%s",
            user_id,
            normalized_channel,
            endpoint_key,
            is_default,
        )
        if not user_id or not normalized_channel or not endpoint_key:
            return rpc_error("VALIDATION_ERROR", "Invalid request payload.")
        if normalized_channel not in self._configured_channels:
            return rpc_error("VALIDATION_ERROR", "Invalid request payload.")

        self._database.attach_channel_endpoint(
            user_id=user_id,
            channel=normalized_channel,
            endpoint_key=endpoint_key,
            is_default=is_default,
        )
        return None

    async def create_subscription(self, body: CreateSubscriptionRequest, user_id: str):
        created, skipped, errors = self._database.create_subscriptions(user_id, body)

        logging.info(
            "create_subscription for user_id=%s created=%s skipped=%s errors=%s",
            user_id,
            len(created),
            len(skipped),
            len(errors),
        )
        return {"created": created, "skipped": skipped, "errors": errors}

    async def list_subscriptions(self, user_id: str):
        logging.info("list_subscriptions for user_id=%s", user_id)
        items = self._database.list_subscriptions(user_id)
        return {"items": items}

    async def update_subscription(
        self,
        subscription_id,
        body: UpdateSubscriptionRequest,
        user_id: str,
    ):
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

    async def delete_subscription(self, subscription_id, user_id: str):
        deleted = self._database.delete_subscription(user_id, subscription_id)
        if not deleted:
            raise NotFoundError("Resource not found.")
        return {"status": "deleted"}

    async def upsert_channel(self):
        raise NotImplementedError

    async def list_channels(self):
        items = []
        for entry in self._configured_channels:
            if isinstance(entry, str):
                channel = entry.strip().lower()
            else:
                channel = ""

            if channel:
                items.append(channel)

        return {"items": items}

    async def update_channel(self):
        raise NotImplementedError

    async def delete_channel(self):
        raise NotImplementedError

    async def list_categories(self):
        raise NotImplementedError
