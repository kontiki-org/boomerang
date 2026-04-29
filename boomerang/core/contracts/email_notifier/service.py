from kontiki.messaging import RpcProxy

EMAIL_NOTIFIER_SERVICE_NAME = "email-notifier-service"

class EmailNotifierRpcProxy(RpcProxy):
    def __init__(self, messenger):
        super().__init__(messenger, EMAIL_NOTIFIER_SERVICE_NAME)
