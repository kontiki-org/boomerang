from kontiki.messaging import RpcProxy


SUBSCRIPTION_SERVICE_NAME = "subscription-service"

class SubscriptionRpcProxy(RpcProxy):
    def __init__(self, messenger):
        super().__init__(messenger, SUBSCRIPTION_SERVICE_NAME)
