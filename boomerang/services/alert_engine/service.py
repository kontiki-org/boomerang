from kontiki.messaging import Messenger, on_event

from boomerang.services.alert_engine.delegate import AlertEngineDelegate


class AlertEngineService:
    name = "alert-engine-service"
    delegate = AlertEngineDelegate()
    messenger = Messenger()

    @on_event("alert.normalized")
    async def on_alert_normalized(self, payload):
        requests = await self.delegate.process_normalized_alert(
            self.messenger, payload
        )
        if not requests:
            return
        for request in requests:
            event_type = f"{request.channel}.alerting.notification.requested"
            await self.messenger.publish(event_type, request.model_dump())

