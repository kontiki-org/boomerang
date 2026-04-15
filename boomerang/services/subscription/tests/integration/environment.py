import os
import time

from kontiki.messaging import on_event
from kontiki.testing import MockService, MockServiceManager, MockServiceRunner


class NotificationEventCatcher(MockService):
    name = "notification-event-catcher"

    @on_event("alerting.notification.requested")
    async def on_notification_requested(self, payload):
        self.event_manager.store_event(
            {"event_type": "alerting.notification.requested", "payload": payload}
        )


def before_all(context):
    time.sleep(1)
    default_config = {"kontiki": {"amqp": {"url": "amqp://guest:guest@localhost"}}}
    context.manager = MockServiceManager(log_file="/tmp/boomerang-integration.log")
    context.manager.add(NotificationEventCatcher, default_config)
    context.runner = MockServiceRunner(context.manager)
    context.runner.start()
    context.runner.ready_event.wait(timeout=10)


def after_scenario(context, scenario):
    _ = scenario
    if hasattr(context, "subscription_process") and context.subscription_process is not None:
        context.subscription_process.terminate()
        context.subscription_process.wait(timeout=5)
        context.subscription_process = None

    if (
        hasattr(context, "subscription_config_path")
        and context.subscription_config_path
        and os.path.isfile(context.subscription_config_path)
    ):
        try:
            os.unlink(context.subscription_config_path)
        except OSError:
            pass
        context.subscription_config_path = None

    if hasattr(context, "manager"):
        context.manager.clean_events("notification-event-catcher")


def after_all(context):
    if hasattr(context, "runner"):
        context.runner.stop()
