import time

from kontiki.testing import MockServiceManager, MockServiceRunner

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
    context.runner = MockServiceRunner(context.manager)
    context.runner.start()
    context.runner.ready_event.wait(timeout=10)


def after_scenario(context, scenario):
    _ = scenario

    if context.email_notifier_process is not None:
        context.email_notifier_process.terminate()
        context.email_notifier_process.wait(timeout=5)
        context.email_notifier_process = None

    app = (context.email_notifier_config or {}).get("app") or {}
    sentinel = app.get("sentinel") or {}
    state_path = sentinel.get("state_path")
    safe_unlink(state_path)
    if state_path:
        safe_unlink(state_path + ".tmp")

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


def after_all(context):
    context.runner.stop()
