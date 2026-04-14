from kontiki.runner import cli
from boomerang.service import AppService


def run():
    cli.run(
        AppService,
        "Example Kontiki-based service.",
        version="0.1.0",
        disable_service_registration=False,
    )
