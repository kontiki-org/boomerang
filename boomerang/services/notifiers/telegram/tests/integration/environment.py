import time

from kontiki.testing import MockServiceManager, MockServiceRunner

from boomerang.services.notifiers.telegram.tests.integration.mocks import TelegramApiMock
from boomerang.testing import NotificationPublisherMock, safe_unlink


def before_all(context):
    time.sleep(1)
    context.telegram_notifier_process = None
    context.telegram_notifier_config_path = None
    context.telegram_notifier_config = None
    context.telegram_notifier_startup_stderr = None
    context.last_http_status = None
    context.last_http_body = None
    context.last_rpc_result = None
    context.last_rpc_error = None
    context.last_published_event_payload = None
    context.last_user_id = None
    context.last_access_token = None

    default_config = {"kontiki": {"amqp": {"url": "amqp://guest:guest@localhost"}}}
    telegram_api_config = {
        "kontiki": {
            "amqp": {"url": "amqp://guest:guest@localhost/"},
            "http": {"address": "127.0.0.1", "port": 9999},
        }
    }
    context.manager = MockServiceManager(log_file="/tmp/boomerang-integration.log")
    context.manager.add(NotificationPublisherMock, default_config)
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

    context.telegram_notifier_config = None
    context.telegram_notifier_startup_stderr = None
    context.last_http_status = None
    context.last_http_body = None
    context.last_rpc_result = None
    context.last_rpc_error = None
    context.last_published_event_payload = None
    context.last_user_id = None
    context.last_access_token = None

    context.manager.clean_http_requests("telegram-api-mock")


def after_all(context):
    context.runner.stop()
