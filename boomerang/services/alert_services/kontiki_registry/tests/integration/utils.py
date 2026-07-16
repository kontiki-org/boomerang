from boomerang.testing import start_kontiki_subprocess


def start_kontiki_registry_alert_subprocess(config):
    return start_kontiki_subprocess(
        "boomerang.services.alert_services.kontiki_registry.service.KontikiRegistryAlertService",
        config,
    )
