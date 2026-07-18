from kontiki.messaging import RpcProxy

KONTIKI_REGISTRY_ALERT_SERVICE_NAME = "kontiki-registry-alert-service"


class KontikiRegistryAlertRpcProxy(RpcProxy):
    def __init__(self, messenger):
        super().__init__(messenger, KONTIKI_REGISTRY_ALERT_SERVICE_NAME)
