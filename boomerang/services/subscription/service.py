from kontiki.messaging import Messenger, rpc, rpc_error
from kontiki.web import http

from boomerang.core.service_contracts.subscription.service import (
    SUBSCRIPTION_SERVICE_NAME,
)
from boomerang.services.subscription.delegates.catalog import (
    CatalogDelegate,
    CatalogNotConfigured,
)
from boomerang.services.subscription.delegates.subscription import SubscriptionDelegate

# -------------------------------------------------------------------------
# Subscription service
# -------------------------------------------------------------------------


class SubscriptionService:
    name = SUBSCRIPTION_SERVICE_NAME
    subscriptions = SubscriptionDelegate()
    catalogs = CatalogDelegate()
    messenger = Messenger()
    http_error_handlers = {
        CatalogNotConfigured: (409, None),
    }

    # -------------------------------------------------------------------------
    # Subscriptions management
    # -------------------------------------------------------------------------

    @rpc
    async def get_recipients_for_alert(self, alert):
        return self.subscriptions.get_recipients_for_alert(alert)

    # -------------------------------------------------------------------------
    # Catalog management
    # -------------------------------------------------------------------------

    @rpc
    async def get_alert_subscription_catalog(self):
        try:
            catalog = await self.catalogs.get_alert_subscription_catalog(self.messenger)
        except CatalogNotConfigured as exc:
            return rpc_error(exc.code, exc.message)
        return catalog.model_dump(mode="json")

    @rpc
    async def get_notification_channels_catalog(self):
        try:
            catalog = await self.catalogs.get_notification_channels_catalog(
                self.messenger
            )
        except CatalogNotConfigured as exc:
            return rpc_error(exc.code, exc.message)
        return catalog.model_dump(mode="json", exclude_none=True)

    @http("/alert-catalog", "GET", version="v1", errors=[CatalogNotConfigured])
    async def get_alert_subscription_catalog_http(self, request):
        _ = request
        catalog = await self.catalogs.get_alert_subscription_catalog(self.messenger)
        return catalog.model_dump(mode="json")

    @http(
        "/notification-channels/catalog",
        "GET",
        version="v1",
        errors=[CatalogNotConfigured],
    )
    async def get_notification_channels_catalog_http(self, request):
        _ = request
        catalog = await self.catalogs.get_notification_channels_catalog(self.messenger)
        return catalog.model_dump(mode="json", exclude_none=True)
