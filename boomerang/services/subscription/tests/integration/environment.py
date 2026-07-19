import time

from kontiki.testing import MockServiceManager, MockServiceRunner

from boomerang.services.subscription.tests.integration.mocks import (
    EarthquakeFeedCatalogMock,
    NotificationEventCatcher,
    WeatherAlertCatalogMock,
)
from boomerang.testing import safe_unlink


def before_all(context):
    time.sleep(1)
    context.subscription_process = None
    context.subscription_config_path = None
    context.subscription_sqlite_path = None
    context.email_notifier_process = None
    context.email_notifier_config_path = None
    context.email_notifier_sqlite_path = None

    default_config = {"kontiki": {"amqp": {"url": "amqp://guest:guest@localhost"}}}
    context.manager = MockServiceManager(log_file="/tmp/boomerang-integration.log")
    context.manager.add(NotificationEventCatcher, default_config)
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

    if context.email_notifier_process is not None:
        context.email_notifier_process.terminate()
        context.email_notifier_process.wait(timeout=5)
        context.email_notifier_process = None

    safe_unlink(context.subscription_config_path)
    context.subscription_config_path = None

    safe_unlink(context.email_notifier_config_path)
    context.email_notifier_config_path = None

    safe_unlink(context.subscription_sqlite_path)
    context.subscription_sqlite_path = None

    safe_unlink(context.email_notifier_sqlite_path)
    context.email_notifier_sqlite_path = None

    context.manager.clean_events("notification-event-catcher")


def after_all(context):
    context.runner.stop()
