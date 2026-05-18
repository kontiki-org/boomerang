import time

from kontiki.testing import MockServiceManager, MockServiceRunner

from boomerang.services.subscription.tests.integration.mocks import (
    EarthquakeFeedCatalogMock,
    NotificationEventCatcher,
    WeatherAlertCatalogMock,
)
from boomerang.testing import IdentityServiceMock
from boomerang.testing import safe_unlink


def before_all(context):
    time.sleep(1)
    context.subscription_process = None
    context.subscription_config_path = None
    context.subscription_sqlite_path = None

    default_config = {"kontiki": {"amqp": {"url": "amqp://guest:guest@localhost"}}}
    context.manager = MockServiceManager(log_file="/tmp/boomerang-integration.log")
    context.manager.add(NotificationEventCatcher, default_config)
    context.manager.add(IdentityServiceMock, default_config)
    context.manager.add(EarthquakeFeedCatalogMock, default_config)
    context.manager.add(WeatherAlertCatalogMock, default_config)
    context.runner = MockServiceRunner(context.manager)
    context.runner.start()
    context.runner.ready_event.wait(timeout=10)


def after_scenario(context, scenario):
    _ = scenario

    if context.subscription_process is not None:
        context.subscription_process.terminate()
        context.subscription_process.wait(timeout=5)
        context.subscription_process = None

    safe_unlink(context.subscription_config_path)
    context.subscription_config_path = None

    safe_unlink(context.subscription_sqlite_path)
    context.subscription_sqlite_path = None

    context.manager.clean_events("notification-event-catcher")
    # Prevent RPC return values/calls from leaking between scenarios.
    context.manager.clean_remote_calls("identity-service")


def after_all(context):
    context.runner.stop()


def before_tag(context, tag):
    if tag.startswith("identity_sessions_"):
        try:
            repeats = int(tag.rsplit("_", 1)[-1])
        except ValueError:
            return
        context.identity_session_repeats = repeats
