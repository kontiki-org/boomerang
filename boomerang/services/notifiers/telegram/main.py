from kontiki.runner import cli

from boomerang import __version__
from boomerang.services.notifiers.telegram.service import TelegramNotifierService


def run() -> None:
    cli.run(
        TelegramNotifierService,
        "Boomerang Telegram Notifier service.",
        version=__version__,
        disable_service_registration=False,
    )


if __name__ == "__main__":
    run()
