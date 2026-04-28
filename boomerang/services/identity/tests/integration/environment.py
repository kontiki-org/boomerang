import time

from kontiki.testing import MockServiceManager, MockServiceRunner

from boomerang.services.identity.tests.integration.mocks import NotificationEventCatcher
from boomerang.testing import EmailNotifierServiceMock, safe_unlink


def before_all(context):
    time.sleep(1)
    context.identity_process = None
    context.identity_config_path = None
    context.identity_sqlite_path = None

    default_config = {"kontiki": {"amqp": {"url": "amqp://guest:guest@localhost"}}}
    context.manager = MockServiceManager(log_file="/tmp/boomerang-integration.log")
    context.manager.add(NotificationEventCatcher, default_config)
    context.manager.add(EmailNotifierServiceMock, default_config)
    context.runner = MockServiceRunner(context.manager)
    context.runner.start()
    context.runner.ready_event.wait(timeout=10)


def before_tag(context, tag):
    prefix = "email_notifier_rpc_ready_"
    if not tag.startswith(prefix):
        return

    try:
        count = int(tag[len(prefix) :])
    except ValueError:
        raise ValueError(
            f"Invalid tag format: {tag}. Expected {prefix}<int>."
        ) from None

    for _ in range(count):
        context.manager.add_remote_return_value(
            "email-notifier-service",
            {
                "endpoint": {
                    "user_id": "placeholder",
                    "endpoint_key": "email_primary",
                    "address": "placeholder@example.org",
                }
            },
        )


def before_scenario(context, scenario):
    _ = (context, scenario)
    return


def after_scenario(context, scenario):
    _ = scenario

    if context.identity_process is not None:
        context.identity_process.terminate()
        context.identity_process.wait(timeout=5)
        context.identity_process = None

    safe_unlink(context.identity_config_path)
    context.identity_config_path = None

    safe_unlink(context.identity_sqlite_path)
    context.identity_sqlite_path = None

    context.manager.clean_events("notification-event-catcher")
    context.manager.clean_remote_calls("email-notifier-service")


def after_all(context):
    if hasattr(context, "runner"):
        context.runner.stop()
