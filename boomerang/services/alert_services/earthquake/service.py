import logging
from kontiki.messaging import Messenger
from kontiki.task.task import task

from boomerang.services.alert_services.earthquake.delegate import EarthquakeFeedDelegate


class EarthquakeFeedService:
    name = "earthquake-feed-service"
    delegate = EarthquakeFeedDelegate()
    messenger = Messenger()

    @task(interval=120, immediate=True)
    async def poll_usgs_and_publish(self) -> None:
        logging.info("Polling USGS and publishing normalized alerts")
        payloads = await self.delegate.build_normalized_alerts()
        for payload in payloads:
            await self.messenger.publish("alert.normalized", payload)
