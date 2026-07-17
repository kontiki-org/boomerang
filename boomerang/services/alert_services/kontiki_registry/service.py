import logging

from kontiki.messaging import Messenger, on_event, rpc
from kontiki.task.task import task

from boomerang.core.contracts.alert_normalized import ALERT_NORMALIZED_EVENT
from boomerang.core.contracts.alert_services.kontiki_registry import (
    KONTIKI_REGISTRY_ALERT_SERVICE_NAME,
)
from boomerang.services.alert_services.kontiki_registry.alert_mapping import (
    REGISTRY_EVENT_EXCEPTION_RECORDED,
    REGISTRY_EVENT_INSTANCE_DEREGISTERED,
    REGISTRY_EVENT_INSTANCE_REGISTERED,
    REGISTRY_EVENT_INSTANCE_STATUS_CHANGED,
)
from boomerang.services.alert_services.kontiki_registry.delegate import (
    KontikiRegistryAlertDelegate,
)
from boomerang.services.alert_services.kontiki_registry.fleet_state import (
    FLEET_POLL_INTERVAL_SECONDS,
)


class KontikiRegistryAlertService:
    name = KONTIKI_REGISTRY_ALERT_SERVICE_NAME
    delegate = KontikiRegistryAlertDelegate()
    messenger = Messenger()

    @rpc
    async def get_alert_subscription_catalog(self):
        return self.delegate.get_alert_subscription_catalog()

    @on_event(REGISTRY_EVENT_INSTANCE_REGISTERED)
    async def on_instance_registered(self, payload):
        await self._publish_normalized_alert(REGISTRY_EVENT_INSTANCE_REGISTERED, payload)

    @on_event(REGISTRY_EVENT_INSTANCE_DEREGISTERED)
    async def on_instance_deregistered(self, payload):
        await self._publish_normalized_alert(
            REGISTRY_EVENT_INSTANCE_DEREGISTERED, payload
        )

    @on_event(REGISTRY_EVENT_INSTANCE_STATUS_CHANGED)
    async def on_instance_status_changed(self, payload):
        await self._publish_normalized_alert(
            REGISTRY_EVENT_INSTANCE_STATUS_CHANGED, payload
        )

    @on_event(REGISTRY_EVENT_EXCEPTION_RECORDED)
    async def on_exception_recorded(self, payload):
        await self._publish_normalized_alert(REGISTRY_EVENT_EXCEPTION_RECORDED, payload)

    @task(interval=FLEET_POLL_INTERVAL_SECONDS, immediate=False)
    async def poll_fleet_state(self):
        alerts = await self.delegate.build_fleet_alerts()
        for alert in alerts:
            logging.info(
                "Publishing fleet alert.normalized event_type=%s alert_id=%s "
                "resolution=%s",
                alert.event_type,
                alert.alert_id,
                alert.attributes.get("resolution"),
            )
            await self.messenger.publish(ALERT_NORMALIZED_EVENT, alert)

    async def _publish_normalized_alert(self, registry_event_type, payload):
        alert = self.delegate.build_normalized_alert(registry_event_type, payload)
        if alert is None:
            return
        logging.info(
            "Publishing alert.normalized for registry event %s alert_id=%s",
            registry_event_type,
            alert.alert_id,
        )
        await self.messenger.publish(ALERT_NORMALIZED_EVENT, alert)
