from kontiki.messaging import RpcProxy

ZULIP_NOTIFIER_SERVICE_NAME = "zulip-notifier-service"


class ZulipNotifierRpcProxy(RpcProxy):
    def __init__(self, messenger):
        super().__init__(messenger, ZULIP_NOTIFIER_SERVICE_NAME)
