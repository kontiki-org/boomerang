from kontiki.runner import cli

from boomerang.services.notifiers.telegram.service import TelegramNotifierService


def run() -> None:
    cli.run(
        TelegramNotifierService,
        "Boomerang Telegram Notifier service.",
        version="0.1.0",
        disable_service_registration=False,
    )


if __name__ == "__main__":
    run()
