import time

from kontiki.testing import MockServiceManager, MockServiceRunner

from boomerang.services.alert_services.earthquake.tests.integration.mocks import (
    AlertNormalizedEventCatcher,
    UsgsFeedMock,
)
from boomerang.testing import safe_unlink


def before_all(context):
    time.sleep(1)
    context.earthquake_feed_process = None
    context.earthquake_feed_config_path = None

    default_config = {"kontiki": {"amqp": {"url": "amqp://guest:guest@localhost/"}}}
    feed_mock_config = {
        "kontiki": {
            "amqp": {"url": "amqp://guest:guest@localhost/"},
            "http": {"address": "127.0.0.1", "port": 18181},
        }
    }
    context.manager = MockServiceManager(log_file="/tmp/boomerang-integration.log")
    context.manager.add(UsgsFeedMock, feed_mock_config)
    context.manager.add(AlertNormalizedEventCatcher, default_config)
    context.runner = MockServiceRunner(context.manager)
    context.runner.start()
    context.runner.ready_event.wait(timeout=10)


def before_scenario(context, scenario):
    _ = scenario
    context.manager.clean_events("alert-normalized-event-catcher")
    context.manager.clean_http_requests("usgs-feed-mock")


def after_scenario(context, scenario):
    _ = scenario
    if getattr(context, "earthquake_feed_process", None) is not None:
        context.earthquake_feed_process.terminate()
        context.earthquake_feed_process.wait(timeout=5)
        context.earthquake_feed_process = None

    safe_unlink(getattr(context, "earthquake_feed_config_path", None))
    context.earthquake_feed_config_path = None
    context.manager.clean_events("alert-normalized-event-catcher")
    context.manager.clean_http_requests("usgs-feed-mock")


def after_all(context):
    context.runner.stop()
