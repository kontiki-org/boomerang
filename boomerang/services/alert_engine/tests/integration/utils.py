from boomerang.testing import start_kontiki_subprocess


def start_alert_engine_subprocess(config):
    return start_kontiki_subprocess(
        "boomerang.services.alert_engine.service.AlertEngineService", config
    )


__all__ = ["start_alert_engine_subprocess"]
