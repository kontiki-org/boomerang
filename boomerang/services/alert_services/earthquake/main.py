from kontiki.runner import cli

from boomerang.services.alert_services.earthquake.service import EarthquakeFeedService


def run() -> None:
    cli.run(
        EarthquakeFeedService,
        "Boomerang earthquake feed connector (USGS -> alert.normalized).",
        version="0.1.0",
        disable_service_registration=False,
    )


if __name__ == "__main__":
    run()
