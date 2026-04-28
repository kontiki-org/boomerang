from kontiki.runner import cli

from boomerang.services.alert_engine.service import AlertEngineService


def run() -> None:
    cli.run(
        AlertEngineService,
        "Boomerang Alert Engine service.",
        version="0.1.0",
        disable_service_registration=False,
    )


if __name__ == "__main__":
    run()
