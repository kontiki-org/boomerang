from kontiki.runner import cli

from boomerang import __version__
from boomerang.services.subscription.service import SubscriptionService


def run():
    cli.run(
        SubscriptionService,
        "Boomerang Subscription Store service.",
        version=__version__,
        disable_service_registration=False,
    )


if __name__ == "__main__":
    run()
