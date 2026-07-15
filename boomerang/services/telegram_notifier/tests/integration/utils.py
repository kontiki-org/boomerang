from boomerang.testing import http_request, start_kontiki_subprocess


def start_telegram_notifier_subprocess(config):
    return start_kontiki_subprocess(
        "boomerang.services.telegram_notifier.service.TelegramNotifierService",
        config,
    )


__all__ = ["http_request", "start_telegram_notifier_subprocess"]
