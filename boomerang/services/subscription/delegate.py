import logging

from boomerang_contracts.alert.catalog import (
    AlertConnectorCatalog,
    AlertSubscriptionCatalog,
)
from boomerang_contracts.alert.normalized import NormalizedAlert
from boomerang_contracts.notification.channel_catalog import (
    NotificationChannelCatalog,
    NotificationChannelsCatalog,
)
from boomerang_contracts.notification.endpoint import (
    CreateChannelEndpointRequest,
    CreateEndpointRequest,
)
from kontiki.configuration.parameter import get_parameter
from kontiki.delegate import ServiceDelegate
from kontiki.messaging import RpcClientError, RpcProxy

from boomerang.core.exceptions import NotFoundError, ValidationError
from boomerang.core.service_contracts.subscription import (
    CreateSubscriptionRequest,
    UpdateSubscriptionRequest,
)
from boomerang.services.subscription.configured_subscriptions import (
    load_configured_subscriptions,
)
from boomerang.services.subscription.database import Database
from boomerang.services.subscription.subscription_resolution import merge_recipients


def _reraise_proxy_rpc_error(exc: RpcClientError) -> None:
    if exc.code == NotFoundError.code:
        raise NotFoundError() from exc
    if exc.code == ValidationError.code:
        raise ValidationError() from exc
    raise exc


def _connector_catalog_from_rpc_result(raw) -> AlertConnectorCatalog:
    if isinstance(raw, AlertConnectorCatalog):
        return raw
    return AlertConnectorCatalog.model_validate(raw)


def _channel_catalog_from_rpc_result(raw) -> NotificationChannelCatalog:
    if isinstance(raw, NotificationChannelCatalog):
        return raw
    return NotificationChannelCatalog.model_validate(raw)


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
        configured_notification_channels = get_parameter(
            self.container.config,
            "app.notification_channels",
            [],
        )
        self._notification_channels = []
        if isinstance(configured_notification_channels, list):
            for entry in configured_notification_channels:
                if isinstance(entry, str):
                    name = entry.strip()
                    if name:
                        self._notification_channels.append(name)
        if self._storage_backend != "sqlite":
            raise RuntimeError("Unsupported storage backend for MVP.")
        self._database = Database(self._sqlite_path)
        self._database.setup()
        configured_subscriptions = get_parameter(
            self.container.config,
            "app.subscriptions",
            None,
        )
        self._configured_subscriptions = load_configured_subscriptions(
            configured_subscriptions
        )
        logging.info(
            "SubscriptionDelegate configured (backend=%s path=%s connectors=%s"
            " notification_channels=%s configured_subscriptions=%s)",
            self._storage_backend,
            self._sqlite_path,
            self._alert_connectors,
            self._notification_channels,
            len(self._configured_subscriptions),
        )

    async def get_alert_subscription_catalog(
        self, messenger
    ) -> AlertSubscriptionCatalog:
        sources: list[AlertConnectorCatalog] = []
        for service_name in self._alert_connectors:
            proxy = RpcProxy(messenger, service_name)
            raw = await proxy.get_alert_subscription_catalog()
            sources.append(_connector_catalog_from_rpc_result(raw))
        return AlertSubscriptionCatalog(sources=sources)

    async def get_notification_channels_catalog(
        self,
        messenger,
    ) -> NotificationChannelsCatalog:
        channels: list[NotificationChannelCatalog] = []
        for service_name in self._notification_channels:
            proxy = RpcProxy(messenger, service_name)
            raw = await proxy.get_notification_channel_catalog()
            channels.append(_channel_catalog_from_rpc_result(raw))
        return NotificationChannelsCatalog(channels=channels)

    async def create_endpoint(
        self,
        body: CreateChannelEndpointRequest,
        user_id: str,
        headers,
        messenger,
    ):
        if not isinstance(body, CreateChannelEndpointRequest):
            body = CreateChannelEndpointRequest.model_validate(body)

        catalog = await self._channel_catalog_for_id(body.channel_id, messenger)
        if catalog is None:
            raise ValidationError()

        request = CreateEndpointRequest(
            endpoint_key=body.endpoint_key,
            fields=body.fields,
        )
        proxy = RpcProxy(messenger, catalog.service_name)
        try:
            result = await proxy.create_endpoint(
                body=request,
                extra_headers=headers,
            )
        except RpcClientError as exc:
            _reraise_proxy_rpc_error(exc)
        return self._with_channel_id(body.channel_id, result)

    async def list_endpoints(self, user_id, headers, messenger):
        _ = user_id
        catalog = await self.get_notification_channels_catalog(messenger)
        endpoints = []
        for channel in catalog.channels:
            proxy = RpcProxy(messenger, channel.service_name)
            try:
                result = await proxy.list_endpoints(extra_headers=headers)
            except RpcClientError as exc:
                _reraise_proxy_rpc_error(exc)
            for endpoint in result.get("endpoints", []):
                endpoints.append(
                    self._endpoint_with_channel(channel.channel_id, endpoint)
                )
        return {"endpoints": endpoints}

    async def get_endpoint(
        self,
        channel_id: str,
        endpoint_key: str,
        user_id,
        headers,
        messenger,
    ):
        _ = user_id
        catalog = await self._channel_catalog_for_id(channel_id, messenger)
        if catalog is None:
            raise ValidationError()

        proxy = RpcProxy(messenger, catalog.service_name)
        try:
            result = await proxy.get_endpoint(
                endpoint_key=endpoint_key,
                extra_headers=headers,
            )
        except RpcClientError as exc:
            _reraise_proxy_rpc_error(exc)
        return self._with_channel_id(channel_id, result)

    async def delete_endpoint(
        self,
        channel_id: str,
        endpoint_key: str,
        user_id,
        headers,
        messenger,
    ):
        _ = user_id
        catalog = await self._channel_catalog_for_id(channel_id, messenger)
        if catalog is None:
            raise ValidationError()

        proxy = RpcProxy(messenger, catalog.service_name)
        try:
            return await proxy.delete_endpoint(
                endpoint_key=endpoint_key,
                extra_headers=headers,
            )
        except RpcClientError as exc:
            _reraise_proxy_rpc_error(exc)

    async def get_recipients_for_alert(self, alert):
        if not isinstance(alert, NormalizedAlert):
            alert = NormalizedAlert.model_validate(alert)
        alert_payload = alert.model_dump(mode="json")
        sqlite_recipients = self._database.get_recipients_for_alert(alert_payload)
        configured_recipients = self._configured_subscriptions.get_recipients_for_alert(
            alert_payload
        )
        return merge_recipients(sqlite_recipients, configured_recipients)

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

    async def _channel_catalog_for_id(
        self,
        channel_id: str,
        messenger,
    ) -> NotificationChannelCatalog | None:
        normalized_channel_id = (channel_id or "").strip().lower()
        if not normalized_channel_id:
            return None
        catalog = await self.get_notification_channels_catalog(messenger)
        for channel in catalog.channels:
            if channel.channel_id == normalized_channel_id:
                return channel
        return None

    def _with_channel_id(self, channel_id: str, result):
        if not isinstance(result, dict):
            return result
        endpoint = result.get("endpoint")
        if isinstance(endpoint, dict):
            enriched = dict(endpoint)
            enriched["channel_id"] = channel_id
            return {"endpoint": enriched}
        return result

    def _endpoint_with_channel(self, channel_id: str, endpoint):
        if not isinstance(endpoint, dict):
            return endpoint
        enriched = dict(endpoint)
        enriched["channel_id"] = channel_id
        return enriched
