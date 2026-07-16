from kontiki.runner import cli

from boomerang.services.alert_services.kontiki_registry.service import (
    KontikiRegistryAlertService,
)


def run() -> None:
    cli.run(
        KontikiRegistryAlertService,
        "Boomerang Kontiki Registry alert connector (registry events -> alert.normalized).",
        version="0.1.0",
        disable_service_registration=False,
    )


if __name__ == "__main__":
    run()
