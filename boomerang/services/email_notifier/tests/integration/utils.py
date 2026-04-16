from boomerang.testing import http_request, start_kontiki_subprocess


def start_email_notifier_subprocess(config):
    return start_kontiki_subprocess(
        "boomerang.services.email_notifier.service.EmailNotifierService", config
    )


__all__ = ["http_request", "start_email_notifier_subprocess"]

