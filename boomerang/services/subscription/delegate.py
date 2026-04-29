import logging

from kontiki.configuration.parameter import get_parameter
from kontiki.delegate import ServiceDelegate

from boomerang.core.contracts.subscription import (
    CreateSubscriptionRequest,
    UpdateSubscriptionRequest,
)
from boomerang.core.exceptions import ValidationError
from boomerang.services.subscription.database import Database
from boomerang.services.subscription.exceptions import NotFoundError


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
        configured_alerts = get_parameter(
            self.container.config, "app.alerts.allowed", []
        )
        self._configured_alerts = (
            configured_alerts if isinstance(configured_alerts, list) else []
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

    async def get_recipients_for_alert(
        self,
        area_type,
        area_value,
        severity,
        category,
        event_type,
    ):
        normalized_area_type = area_type.strip().lower()
        normalized_area_value = area_value.strip()
        normalized_severity = severity.strip().lower()
        normalized_category = category.strip().lower()
        normalized_event_type = event_type.strip().lower()
        if (
            not normalized_area_type
            or not normalized_area_value
            or not normalized_severity
            or not normalized_category
            or not normalized_event_type
        ):
            return []
        return self._database.get_recipients_for_alert(
            area_type=normalized_area_type,
            area_value=normalized_area_value,
            severity=normalized_severity,
            category=normalized_category,
            event_type=normalized_event_type,
        )

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
            raise ValidationError()
        if normalized_channel not in self._configured_channels:
            raise ValidationError()

        self._database.attach_channel_endpoint(
            user_id=user_id,
            channel=normalized_channel,
            endpoint_key=endpoint_key,
            is_default=is_default,
        )

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

    async def get_subscriptions(self, user_id: str):
        logging.info("get_subscriptions for user_id=%s", user_id)
        items = self._database.get_subscriptions(user_id)
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
            raise NotFoundError()
        return {"status": "ok", "item": updated}

    async def delete_subscription(self, subscription_id, user_id: str):
        deleted = self._database.delete_subscription(user_id, subscription_id)
        if not deleted:
            raise NotFoundError()
        return {"status": "deleted"}

    async def get_channels(self):
        items = []
        for entry in self._configured_channels:
            if isinstance(entry, str):
                channel = entry.strip().lower()
            else:
                channel = ""

            if channel:
                items.append(channel)

        return {"items": items}

    async def get_alerts(self):
        items = []
        for entry in self._configured_alerts:
            if not isinstance(entry, dict):
                continue
            raw_category = entry.get("category")
            raw_event_type = entry.get("event_type")
            if not isinstance(raw_category, str) or not isinstance(raw_event_type, str):
                continue
            category = raw_category.strip().lower()
            event_type = raw_event_type.strip().lower()
            if category and event_type:
                items.append({"category": category, "event_type": event_type})

        return {"items": items}
