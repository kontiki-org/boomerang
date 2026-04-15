from kontiki.runner import cli

from boomerang.services.subscription.service import SubscriptionService


def run():
    cli.run(
        SubscriptionService,
        "Boomerang Subscription Store service.",
        version="0.1.0",
        disable_service_registration=False,
    )


if __name__ == "__main__":
    run()
