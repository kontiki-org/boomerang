from kontiki.messaging import on_event
from kontiki.testing import MockService


class AlertNormalizedEventCatcher(MockService):
    name = "alert-normalized-event-catcher"

    @on_event("alert.normalized")
    async def on_alert_normalized(self, payload):
        self.event_manager.store_event(
            {"event_type": "alert.normalized", "payload": payload}
        )
