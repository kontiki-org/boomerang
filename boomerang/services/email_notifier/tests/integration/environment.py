import time

from kontiki.testing import MockServiceManager, MockServiceRunner

from boomerang.services.email_notifier.tests.integration.mocks import (
    NotificationOutcomeCatcher,
)
from boomerang.testing import (
    IdentityServiceMock,
    NotificationPublisherMock,
    safe_unlink,
)


def before_all(context):
    time.sleep(1)
    context.email_notifier_process = None
    context.email_notifier_config_path = None
    context.email_notifier_sqlite_path = None

    default_config = {"kontiki": {"amqp": {"url": "amqp://guest:guest@localhost"}}}
    context.manager = MockServiceManager(log_file="/tmp/boomerang-integration.log")
    context.manager.add(IdentityServiceMock, default_config)
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

    safe_unlink(context.email_notifier_sqlite_path)
    context.email_notifier_sqlite_path = None

    # Prevent RPC return values/calls from leaking between scenarios.
    context.manager.clean_remote_calls("identity-service")
    context.manager.clean_events("notification-outcome-catcher")


def after_all(context):
    context.runner.stop()


def before_tag(context, tag):
    if tag.startswith("identity_sessions_"):
        try:
            repeats = int(tag.rsplit("_", 1)[-1])
        except ValueError:
            return
        context.identity_session_repeats = repeats
