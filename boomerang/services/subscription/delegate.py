import logging

from kontiki.configuration.parameter import get_parameter
from kontiki.delegate import ServiceDelegate
from kontiki.messaging import RpcProxy

from boomerang.core.contracts.alert_catalog import (
    AlertConnectorCatalog,
    AlertSubscriptionCatalog,
)
from boomerang.core.contracts.alert_normalized import NormalizedAlert
from boomerang.core.contracts.subscription import (
    CreateSubscriptionRequest,
    UpdateSubscriptionRequest,
)
from boomerang.core.exceptions import NotFoundError, ValidationError
from boomerang.services.subscription.database import Database


def _connector_catalog_from_rpc_result(raw) -> AlertConnectorCatalog:
    if isinstance(raw, AlertConnectorCatalog):
        return raw
    return AlertConnectorCatalog.model_validate(raw)


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
        configured_connectors = get_parameter(
            self.container.config, "app.alert_connectors", []
        )
        self._alert_connectors = []
        if isinstance(configured_connectors, list):
            for entry in configured_connectors:
                if isinstance(entry, str):
                    name = entry.strip()
                    if name:
                        self._alert_connectors.append(name)
        if self._storage_backend != "sqlite":
            raise RuntimeError("Unsupported storage backend for MVP.")
        self._database = Database(self._sqlite_path)
        self._database.setup()
        logging.info(
            "SubscriptionDelegate configured (backend=%s path=%s connectors=%s)",
            self._storage_backend,
            self._sqlite_path,
            self._alert_connectors,
        )

    async def get_alert_subscription_catalog(self, messenger) -> AlertSubscriptionCatalog:
        sources: list[AlertConnectorCatalog] = []
        for service_name in self._alert_connectors:
            proxy = RpcProxy(messenger, service_name)
            raw = await proxy.get_alert_subscription_catalog()
            sources.append(_connector_catalog_from_rpc_result(raw))
        return AlertSubscriptionCatalog(sources=sources)

    async def get_recipients_for_alert(self, alert):
        if not isinstance(alert, NormalizedAlert):
            alert = NormalizedAlert.model_validate(alert)
        return self._database.get_recipients_for_alert(alert.model_dump(mode="json"))

    async def attach_channel_endpoint(
        self,
        user_id: str,
        channel: str,
        endpoint_key: str,
        is_default: bool = False,
    ):
        _ = (user_id, channel, endpoint_key, is_default)
        raise ValidationError()

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
            body=body,
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
