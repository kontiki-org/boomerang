from boomerang.testing import http_request, start_kontiki_subprocess


def start_sms_notifier_subprocess(config):
    return start_kontiki_subprocess(
        "boomerang.services.sms_notifier.service.SmsNotifierService", config
    )


__all__ = ["http_request", "start_sms_notifier_subprocess"]

