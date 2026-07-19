import time

from kontiki.testing import MockServiceManager, MockServiceRunner

from boomerang.services.notifiers.email.tests.integration.mocks import (
    NotificationOutcomeCatcher,
)
from boomerang.testing import NotificationPublisherMock, safe_unlink


def before_all(context):
    time.sleep(1)
    context.email_notifier_process = None
    context.email_notifier_config_path = None
    context.email_notifier_config = None
    context.email_notifier_startup_stderr = None
    context.last_http_status = None
    context.last_http_body = None
    context.last_rpc_result = None
    context.last_rpc_error = None
    context.last_published_event_payload = None
    context.last_user_id = None
    context.last_access_token = None

    default_config = {"kontiki": {"amqp": {"url": "amqp://guest:guest@localhost"}}}
    context.manager = MockServiceManager(log_file="/tmp/boomerang-integration.log")
    context.manager.add(NotificationPublisherMock, default_config)
    context.manager.add(NotificationOutcomeCatcher, default_config)
    context.runner = MockServiceRunner(context.manager)
    context.runner.start()
    context.runner.ready_event.wait(timeout=10)


def after_scenario(context, scenario):
    _ = scenario

    if context.email_notifier_process is not None:
        context.email_notifier_process.terminate()
        context.email_notifier_process.wait(timeout=5)
        context.email_notifier_process = None

    safe_unlink(context.email_notifier_config_path)
    context.email_notifier_config_path = None

    context.email_notifier_config = None
    context.email_notifier_startup_stderr = None
    context.last_http_status = None
    context.last_http_body = None
    context.last_rpc_result = None
    context.last_rpc_error = None
    context.last_published_event_payload = None
    context.last_user_id = None
    context.last_access_token = None

    context.manager.clean_events("notification-outcome-catcher")


def after_all(context):
    context.runner.stop()
