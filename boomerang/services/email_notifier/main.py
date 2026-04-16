from kontiki.runner import cli

from boomerang.services.email_notifier.service import EmailNotifierService


def run() -> None:
    cli.run(
        EmailNotifierService,
        "Boomerang Email Notifier service.",
        version="0.1.0",
        disable_service_registration=False,
    )


if __name__ == "__main__":
    run()
