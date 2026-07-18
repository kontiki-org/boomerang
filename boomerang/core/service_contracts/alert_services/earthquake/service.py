from kontiki.messaging import RpcProxy

EARTHQUAKE_FEED_SERVICE_NAME = "earthquake-feed-service"


class EarthquakeFeedRpcProxy(RpcProxy):
    def __init__(self, messenger):
        super().__init__(messenger, EARTHQUAKE_FEED_SERVICE_NAME)
