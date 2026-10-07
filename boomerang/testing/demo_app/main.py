from kontiki.runner import cli

from boomerang import __version__
from boomerang.testing.demo_app.service import DemoAppService


def run():
    cli.run(
        DemoAppService,
        "Demo Kontiki app for Registry alerting (embedded profile).",
        version=__version__,
        disable_service_registration=False,
    )


if __name__ == "__main__":
    run()
