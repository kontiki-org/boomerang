from kontiki.runner import cli

from boomerang import __version__
from boomerang.services.notifiers.zulip.service import ZulipNotifierService


def run():
    cli.run(
        ZulipNotifierService,
        "Boomerang Zulip Notifier service.",
        version=__version__,
        disable_service_registration=False,
    )


if __name__ == "__main__":
    run()
