import time

from kontiki.testing import MockServiceManager, MockServiceRunner

from boomerang.services.telegram_notifier.tests.integration.mocks import (
    NotificationOutcomeCatcher,
    TelegramApiMock,
)
from boomerang.testing import IdentityServiceMock, NotificationPublisherMock, safe_unlink


def before_all(context):
    time.sleep(1)
    context.telegram_notifier_process = None
    context.telegram_notifier_config_path = None
    context.telegram_notifier_sqlite_path = None

    default_config = {"kontiki": {"amqp": {"url": "amqp://guest:guest@localhost"}}}
    telegram_api_config = {
        "kontiki": {
            "amqp": {"url": "amqp://guest:guest@localhost/"},
            "http": {"address": "127.0.0.1", "port": 9999},
        }
    }
    context.manager = MockServiceManager(log_file="/tmp/boomerang-integration.log")
    context.manager.add(IdentityServiceMock, default_config)
    context.manager.add(NotificationPublisherMock, default_config)
    context.manager.add(NotificationOutcomeCatcher, default_config)
    context.manager.add(TelegramApiMock, telegram_api_config)
    context.runner = MockServiceRunner(context.manager)
    context.runner.start()
    context.runner.ready_event.wait(timeout=10)


def after_scenario(context, scenario):
    _ = scenario

    if context.telegram_notifier_process is not None:
        context.telegram_notifier_process.terminate()
        context.telegram_notifier_process.wait(timeout=5)
        context.telegram_notifier_process = None

    safe_unlink(context.telegram_notifier_config_path)
    context.telegram_notifier_config_path = None

    safe_unlink(context.telegram_notifier_sqlite_path)
    context.telegram_notifier_sqlite_path = None

    context.manager.clean_remote_calls("identity-service")
    context.manager.clean_events("notification-outcome-catcher")
    context.manager.clean_http_requests("telegram-api-mock")


def after_all(context):
    context.runner.stop()


def before_tag(context, tag):
    if tag.startswith("identity_sessions_"):
        try:
            repeats = int(tag.rsplit("_", 1)[-1])
        except ValueError:
            return
        context.identity_session_repeats = repeats
