from kontiki.runner import cli

from boomerang import __version__
from boomerang.services.notifiers.ntfy.service import NtfyNotifierService


def run():
    cli.run(
        NtfyNotifierService,
        "Boomerang ntfy Notifier service.",
        version=__version__,
        disable_service_registration=False,
    )


if __name__ == "__main__":
    run()
