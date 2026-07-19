from boomerang.services.email_notifier.tests.integration.utils import (
    start_email_notifier_subprocess,
)
from boomerang.testing import http_request, start_kontiki_subprocess


def start_subscription_subprocess(config):
    return start_kontiki_subprocess(
        "boomerang.services.subscription.service.SubscriptionService", config
    )


def email_notifier_config_for_subscription_tests():
    return {
        "kontiki": {
            "amqp": {"url": "amqp://guest:guest@localhost/"},
            "http": {"address": "127.0.0.1", "port": 8001},
        },
        "logging": {
            "version": 1,
            "disable_existing_loggers": False,
            "formatters": {
                "default": {
                    "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
                    "datefmt": "%Y-%m-%d %H:%M:%S",
                }
            },
            "handlers": {
                "file": {
                    "class": "logging.FileHandler",
                    "formatter": "default",
                    "filename": "/tmp/email-notifier-subscription-proxy.log",
                    "level": "INFO",
                }
            },
            "root": {"level": "DEBUG", "handlers": ["file"]},
        },
        "app": {
            "storage": {
                "backend": "sqlite",
                "sqlite_path": (
                    "boomerang/services/subscription/tests/integration/db/"
                    "email_notifier.sqlite3"
                ),
            },
            "email": {
                "smtp": {
                    "host": "smtp.example.org",
                    "port": 587,
                    "use_starttls": True,
                    "username": "smtp-user",
                    "password": "smtp-password",
                },
                "from": {"address": "no-reply@example.org"},
            },
        },
    }


def configured_notification_channels(config):
    channels = config.get("app", {}).get("notification_channels", [])
    if not isinstance(channels, list):
        return []
    names = []
    for entry in channels:
        if isinstance(entry, str):
            name = entry.strip()
            if name:
                names.append(name)
    return names


__all__ = [
    "configured_notification_channels",
    "email_notifier_config_for_subscription_tests",
    "http_request",
    "start_email_notifier_subprocess",
    "start_subscription_subprocess",
]
