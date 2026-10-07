from kontiki.runner import cli

from boomerang import __version__
from boomerang.services.alert_engine.service import AlertEngineService


def run() -> None:
    cli.run(
        AlertEngineService,
        "Boomerang Alert Engine service.",
        version=__version__,
        disable_service_registration=False,
    )


if __name__ == "__main__":
    run()
