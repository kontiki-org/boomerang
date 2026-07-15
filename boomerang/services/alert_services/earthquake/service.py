import logging

from kontiki.messaging import Messenger, rpc
from kontiki.task.task import task

from boomerang.core.contracts.alert_normalized import ALERT_NORMALIZED_EVENT
from boomerang.core.contracts.alert_services.earthquake import (
    EARTHQUAKE_FEED_SERVICE_NAME,
)
from boomerang.services.alert_services.earthquake.delegate import EarthquakeFeedDelegate


class EarthquakeFeedService:
    name = EARTHQUAKE_FEED_SERVICE_NAME
    delegate = EarthquakeFeedDelegate()
    messenger = Messenger()

    @rpc
    async def get_alert_subscription_catalog(self):
        return self.delegate.get_alert_subscription_catalog()

    @task(interval=120, immediate=True)
    async def poll_usgs_and_publish(self) -> None:
        logging.info("Polling USGS and publishing normalized alerts")
        alerts = await self.delegate.build_normalized_alerts()
        for alert in alerts:
            await self.messenger.publish(ALERT_NORMALIZED_EVENT, alert)
