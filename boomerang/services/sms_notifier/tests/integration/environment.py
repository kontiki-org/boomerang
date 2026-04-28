import time

from kontiki.testing import MockServiceManager, MockServiceRunner

from boomerang.services.sms_notifier.tests.integration.mocks import (
    NotificationOutcomeCatcher,
    SmsProviderMock,
)
from boomerang.testing import (
    IdentityServiceMock,
    NotificationPublisherMock,
    safe_unlink,
)


def before_all(context):
    time.sleep(1)
    context.sms_notifier_process = None
    context.sms_notifier_config_path = None
    context.sms_notifier_sqlite_path = None

    default_config = {"kontiki": {"amqp": {"url": "amqp://guest:guest@localhost"}}}
    sms_provider_config = {
        "kontiki": {
            "amqp": {"url": "amqp://guest:guest@localhost/"},
            "http": {"address": "127.0.0.1", "port": 18080},
        }
    }
    context.manager = MockServiceManager(log_file="/tmp/boomerang-integration.log")
    context.manager.add(IdentityServiceMock, default_config)
    context.manager.add(NotificationPublisherMock, default_config)
    context.manager.add(NotificationOutcomeCatcher, default_config)
    context.manager.add(SmsProviderMock, sms_provider_config)
    context.runner = MockServiceRunner(context.manager)
    context.runner.start()
    context.runner.ready_event.wait(timeout=10)


def after_scenario(context, scenario):
    _ = scenario
    if context.sms_notifier_process is not None:
        context.sms_notifier_process.terminate()
        context.sms_notifier_process.wait(timeout=5)
        context.sms_notifier_process = None

    safe_unlink(context.sms_notifier_config_path)
    context.sms_notifier_config_path = None
    safe_unlink(context.sms_notifier_sqlite_path)
    context.sms_notifier_sqlite_path = None
    context.manager.clean_remote_calls("identity-service")
    context.manager.clean_events("notification-outcome-catcher")
    context.manager.clean_http_requests("sms-provider-service")


def after_all(context):
    context.runner.stop()


def before_tag(context, tag):
    if tag.startswith("identity_sessions_"):
        try:
            repeats = int(tag.rsplit("_", 1)[-1])
        except ValueError:
            return
        context.identity_session_repeats = repeats
