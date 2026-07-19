from kontiki.messaging import Messenger, rpc
from kontiki.web import http

from boomerang.core.service_contracts.subscription.service import SUBSCRIPTION_SERVICE_NAME
from boomerang.services.subscription.delegate import SubscriptionDelegate


class SubscriptionService:
    name = SUBSCRIPTION_SERVICE_NAME
    delegate = SubscriptionDelegate()
    messenger = Messenger()

    @rpc
    async def get_recipients_for_alert(self, alert):
        return await self.delegate.get_recipients_for_alert(alert=alert)

    @rpc
    async def attach_channel_endpoint(
        self,
        user_id: str,
        channel: str,
        endpoint_key: str,
        is_default: bool = False,
    ):
        return await self.delegate.attach_channel_endpoint(
            user_id=user_id,
            channel=channel,
            endpoint_key=endpoint_key,
            is_default=is_default,
        )

    @rpc
    async def get_alert_subscription_catalog(self):
        catalog = await self.delegate.get_alert_subscription_catalog(self.messenger)
        return catalog.model_dump(mode="json")

    @rpc
    async def get_notification_channels_catalog(self):
        catalog = await self.delegate.get_notification_channels_catalog(self.messenger)
        return catalog.model_dump(mode="json", exclude_none=True)

    @http("/alert-catalog", "GET", version="v1")
    async def get_alert_subscription_catalog_http(self, request):
        _ = request
        catalog = await self.delegate.get_alert_subscription_catalog(self.messenger)
        return catalog.model_dump(mode="json")

    @http("/notification-channels/catalog", "GET", version="v1")
    async def get_notification_channels_catalog_http(self, request):
        _ = request
        catalog = await self.delegate.get_notification_channels_catalog(self.messenger)
        return catalog.model_dump(mode="json", exclude_none=True)
