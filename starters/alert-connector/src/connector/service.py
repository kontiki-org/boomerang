import logging

from connector import SERVICE_NAME
from connector.delegate import ConnectorDelegate
from kontiki.messaging import Messenger, rpc

from boomerang.core.contracts.alert_normalized import ALERT_NORMALIZED_EVENT


class ConnectorService:
    """Demo alert producer for the Starter Kit.

    ``emit_demo_alert`` is pedagogical only. Real connectors replace it with a
    domain mechanism (@task polling, @on_event, webhook, …).
    """

    name = SERVICE_NAME
    delegate = ConnectorDelegate()
    messenger = Messenger()

    @rpc
    async def get_alert_subscription_catalog(self):
        return self.delegate.get_alert_subscription_catalog()

    @rpc
    async def emit_demo_alert(self):
        alert = self.delegate.build_demo_alert()
        logging.info(
            "Publishing pedagogical demo alert.normalized alert_id=%s",
            alert.alert_id,
        )
        await self.messenger.publish(ALERT_NORMALIZED_EVENT, alert)
        return alert
