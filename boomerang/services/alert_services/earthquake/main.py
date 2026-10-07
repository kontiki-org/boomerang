from kontiki.runner import cli

from boomerang import __version__
from boomerang.services.alert_services.earthquake.service import EarthquakeFeedService


def run() -> None:
    cli.run(
        EarthquakeFeedService,
        "Boomerang earthquake feed connector (USGS -> alert.normalized).",
        version=__version__,
        disable_service_registration=False,
    )


if __name__ == "__main__":
    run()
