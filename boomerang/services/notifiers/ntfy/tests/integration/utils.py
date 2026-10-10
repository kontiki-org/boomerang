from boomerang.testing import http_request, start_kontiki_subprocess


def start_ntfy_notifier_subprocess(config):
    return start_kontiki_subprocess(
        "boomerang.services.notifiers.ntfy.service.NtfyNotifierService",
        config,
    )


__all__ = ["http_request", "start_ntfy_notifier_subprocess"]
