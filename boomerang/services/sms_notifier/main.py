from kontiki.runner import cli

from boomerang.services.sms_notifier.service import SmsNotifierService


def run() -> None:
    cli.run(
        SmsNotifierService,
        "Boomerang SMS Notifier service.",
        version="0.1.0",
        disable_service_registration=False,
    )


if __name__ == "__main__":
    run()
