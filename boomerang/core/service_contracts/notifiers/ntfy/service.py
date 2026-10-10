from kontiki.messaging import RpcProxy

NTFY_NOTIFIER_SERVICE_NAME = "ntfy-notifier-service"


class NtfyNotifierRpcProxy(RpcProxy):
    def __init__(self, messenger):
        super().__init__(messenger, NTFY_NOTIFIER_SERVICE_NAME)
