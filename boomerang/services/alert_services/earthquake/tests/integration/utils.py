from boomerang.testing import start_kontiki_subprocess


def start_earthquake_feed_subprocess(config):
    return start_kontiki_subprocess(
        "boomerang.services.alert_services.earthquake.service.EarthquakeFeedService",
        config,
    )


__all__ = ["start_earthquake_feed_subprocess"]
