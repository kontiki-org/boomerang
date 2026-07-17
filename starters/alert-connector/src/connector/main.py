from connector.service import ConnectorService
from kontiki.runner import cli


def run() -> None:
    cli.run(
        ConnectorService,
        "Boomerang alert connector starter (demo producer → alert.normalized).",
        version="0.1.0",
        disable_service_registration=False,
    )


if __name__ == "__main__":
    run()
