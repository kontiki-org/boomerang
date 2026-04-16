from kontiki.runner import cli

from boomerang.services.identity.service import IdentityService


def run():
    cli.run(
        IdentityService,
        "Boomerang Identity service.",
        version="0.1.0",
        disable_service_registration=False,
    )


if __name__ == "__main__":
    run()
