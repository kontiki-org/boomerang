import time

from kontiki.testing import MockServiceManager, MockServiceRunner

from boomerang.services.alert_engine.tests.integration.mocks import (
    NotificationDispatchEventCatcher,
    SubscriptionServiceMock,
)
from boomerang.testing import NotificationPublisherMock, safe_unlink

SUBSCRIPTION_RECIPIENT_PRESETS = {
    "subscription_recipients_two": [
        {
            "recipient_id": "usr_1",
            "channel": "email",
            "endpoint_key": "email_primary",
        },
        {
            "recipient_id": "usr_1",
            "channel": "sms",
            "endpoint_key": "sms_primary",
        },
        {
            "recipient_id": "usr_2",
            "channel": "sms",
            "endpoint_key": "sms_backup",
        },
    ],
    "subscription_recipients_none": [],
}


def before_all(context):
    time.sleep(1)
    context.alert_engine_process = None
    context.alert_engine_config_path = None

    default_config = {"kontiki": {"amqp": {"url": "amqp://guest:guest@localhost/"}}}
    context.manager = MockServiceManager(log_file="/tmp/boomerang-integration.log")
    context.manager.add(NotificationPublisherMock, default_config)
    context.manager.add(SubscriptionServiceMock, default_config)
    context.manager.add(NotificationDispatchEventCatcher, default_config)
    context.runner = MockServiceRunner(context.manager)
    context.runner.start()
    context.runner.ready_event.wait(timeout=10)


def after_scenario(context, scenario):
    _ = scenario
    if context.alert_engine_process is not None:
        context.alert_engine_process.terminate()
        context.alert_engine_process.wait(timeout=5)
        context.alert_engine_process = None

    safe_unlink(context.alert_engine_config_path)
    context.alert_engine_config_path = None
    context.manager.clean_remote_calls("subscription-service")
    context.manager.clean_events("notification-dispatch-event-catcher")


def after_all(context):
    context.runner.stop()


def before_tag(context, tag):
    if not tag.startswith("subscription_recipients_"):
        return
    if tag not in SUBSCRIPTION_RECIPIENT_PRESETS:
        raise RuntimeError(f"Unknown recipients preset tag: {tag}")
    recipients = SUBSCRIPTION_RECIPIENT_PRESETS[tag]
    context.expected_subscription_recipients = recipients
    context.manager.add_remote_return_value("subscription-service", recipients)
