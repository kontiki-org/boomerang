from kontiki.runner import cli

from boomerang import __version__
from boomerang.services.notifiers.email.service import EmailNotifierService


def run() -> None:
    cli.run(
        EmailNotifierService,
        "Boomerang Email Notifier service.",
        version=__version__,
        disable_service_registration=False,
    )


if __name__ == "__main__":
    run()
