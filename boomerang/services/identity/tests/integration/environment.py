import time

from kontiki.testing import MockServiceManager, MockServiceRunner

from boomerang.services.identity.tests.integration.mocks import NotificationEventCatcher
from boomerang.services.identity.tests.integration.utils import _safe_unlink


def before_all(context):
    time.sleep(1)
    context.identity_process = None
    context.identity_config_path = None
    context.identity_sqlite_path = None

    default_config = {"kontiki": {"amqp": {"url": "amqp://guest:guest@localhost"}}}
    context.manager = MockServiceManager(log_file="/tmp/boomerang-integration.log")
    context.manager.add(NotificationEventCatcher, default_config)
    context.runner = MockServiceRunner(context.manager)
    context.runner.start()
    context.runner.ready_event.wait(timeout=10)


def after_scenario(context, scenario):
    _ = scenario

    if context.identity_process is not None:
        context.identity_process.terminate()
        context.identity_process.wait(timeout=5)
        context.identity_process = None

    _safe_unlink(context.identity_config_path)
    context.identity_config_path = None

    _safe_unlink(context.identity_sqlite_path)
    context.identity_sqlite_path = None

    context.manager.clean_events("notification-event-catcher")


def after_all(context):
    context.runner.stop()
