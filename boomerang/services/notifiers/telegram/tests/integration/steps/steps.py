import asyncio
import json
import time

import yaml
from behave import given, then, when
from boomerang_contracts.notification.message import NotificationRequest
from kontiki.messaging import Messenger, RpcClientError
from kontiki.registry.client.proxy import ServiceRegistryProxy
from pydantic import BaseModel

from boomerang.services.notifiers.telegram.tests.integration.utils import (
    http_request,
    start_telegram_notifier_subprocess,
)
from boomerang.testing import safe_unlink


def _resolve_placeholders(value, context):
    if not isinstance(value, str):
        return value
    resolved = value
    if context.last_user_id is not None:
        resolved = resolved.replace("[USER_ID]", context.last_user_id)
    if context.last_access_token is not None:
        resolved = resolved.replace("[LAST_ACCESS_TOKEN]", context.last_access_token)
    return resolved


def _normalize_actual_for_placeholders(expected, actual):
    if isinstance(expected, dict) and isinstance(actual, dict):
        normalized = {}
        for key, expected_value in expected.items():
            if key in actual:
                normalized[key] = _normalize_actual_for_placeholders(
                    expected_value, actual[key]
                )
        return normalized

    if isinstance(expected, list) and isinstance(actual, list):
        normalized = []
        for idx, expected_item in enumerate(expected):
            if idx < len(actual):
                normalized.append(
                    _normalize_actual_for_placeholders(expected_item, actual[idx])
                )
        return normalized

    if isinstance(expected, str) and isinstance(actual, str):
        if expected.startswith("[") and expected.endswith("]"):
            return expected
    return actual


def _as_jsonable(value):
    if isinstance(value, BaseModel):
        return value.model_dump(mode="json")
    return value


def _registry_amqp_url(context):
    config = context.telegram_notifier_config or {}
    return (
        config.get("kontiki", {}).get("amqp", {}).get("url")
        or "amqp://guest:guest@localhost/"
    )


def _clear_sentinel_state(config):
    app = config.get("app") if config else None
    sentinel = app.get("sentinel") if app else None
    if not sentinel:
        return
    path = sentinel.get("state_path")
    safe_unlink(path)
    if path:
        safe_unlink(path + ".tmp")


def _start_telegram_notifier(context, config, clear_state):
    if clear_state:
        _clear_sentinel_state(config)
    context.manager.clean_http_requests("telegram-api-mock")
    proc, config_path = start_telegram_notifier_subprocess(config)
    context.telegram_notifier_process = proc
    context.telegram_notifier_config_path = config_path
    time.sleep(5)
    if proc.poll() is not None:
        stderr = (
            proc.stderr.read().decode(errors="replace") if proc.stderr else ""
        ) or "(empty)"
        raise RuntimeError(
            "TelegramNotifier subprocess exited before step. stderr:\n%s" % stderr
        )


def _fetch_registry_services(amqp_url):
    async def _fetch():
        async with Messenger(amqp_url=amqp_url, standalone=True) as messenger:
            proxy = ServiceRegistryProxy(messenger)
            return await proxy.get_services()

    return asyncio.run(_fetch())


@given("the telegram-notifier service is running with the following configuration")
def step_telegram_notifier_running_with_config(context):
    config_text = context.text.strip()
    config = yaml.safe_load(config_text) or {}
    context.telegram_notifier_config = config
    _start_telegram_notifier(context, config, clear_state=True)


@when('an "{event_type}" event is published with payload')
def step_publish_event_with_payload(context, event_type):
    payload = json.loads(context.text.strip()) if context.text else {}
    context.manager.clean_http_requests("telegram-api-mock")
    context.last_published_event_payload = payload
    request_payload = NotificationRequest.model_validate(payload)
    context.runner.call(
        "notification-publisher",
        "publish_event",
        event_type=event_type,
        payload=request_payload,
    )
    time.sleep(1)


@when(
    "I call {method} on the telegram-notifier service on {url} with the following request"
)
def step_call_request_on_telegram_notifier_service_with_request(context, method, url):
    payload = json.loads(context.text.strip()) if context.text else {}
    headers = payload.get("headers")
    body = payload.get("payload")
    if context.last_access_token is not None:
        headers = headers or {}
        headers.setdefault("Authorization", f"Bearer {context.last_access_token}")
    status, resp_body = http_request(method, url, payload=body, headers=headers)
    context.last_http_status = status
    context.last_http_body = resp_body


@when("I wait {seconds:d} second")
@when("I wait {seconds:d} seconds")
def step_wait_seconds(context, seconds):
    _ = context
    time.sleep(seconds)


@when("the telegram-notifier service is restarted")
def step_telegram_notifier_restarted(context):
    proc = context.telegram_notifier_process
    proc.terminate()
    proc.wait(timeout=5)
    safe_unlink(context.telegram_notifier_config_path)
    context.telegram_notifier_process = None
    _start_telegram_notifier(
        context, context.telegram_notifier_config, clear_state=False
    )


@then("the HTTP response status is {status:d}")
def step_http_response_status(context, status):
    assert context.last_http_status == status, "Expected HTTP %s, got %s body=%s" % (
        status,
        context.last_http_status,
        context.last_http_body,
    )


@when(
    "I call the RPC {method_name} on the telegram-notifier service with the following arguments"
)
def step_call_rpc_on_telegram_notifier_service(context, method_name):
    payload_text = _resolve_placeholders(context.text.strip(), context)
    payload = json.loads(payload_text) if payload_text else {}
    extra_headers = None
    if isinstance(payload, dict) and "headers" in payload:
        extra_headers = payload.pop("headers")
    context.last_rpc_error = None
    try:
        context.last_rpc_result = context.runner.call(
            "telegram-notifier-service",
            method_name,
            extra_headers=extra_headers,
            **payload,
        )
    except Exception as exc:
        context.last_rpc_result = None
        context.last_rpc_error = exc


@then("the RPC response is")
def step_rpc_response(context):
    expected = json.loads(context.text.strip()) if context.text else {}
    if context.last_rpc_error is not None:
        raise AssertionError(
            f"Expected RPC success, got error: {context.last_rpc_error}"
        )
    actual = _as_jsonable(context.last_rpc_result)
    normalized_actual = _normalize_actual_for_placeholders(expected, actual)
    assert (
        normalized_actual == expected
    ), f"RPC response mismatch.\nExpected: {expected}\nActual:   {normalized_actual}"


@then("the RPC request is rejected due to validation error")
def step_rpc_validation_error(context):
    expected = json.loads(context.text.strip()) if context.text else {}
    error = context.last_rpc_error
    assert error is not None, "Expected RPC validation error, but call succeeded."
    assert isinstance(error, RpcClientError)
    actual = {"code": error.code, "message": error.message}
    assert (
        actual == expected
    ), f"RPC error mismatch.\nExpected: {expected}\nActual:   {actual}"


@then("the RPC call fails with a {error_code}")
def step_rpc_call_fails_with_error_code(context, error_code):
    expected = json.loads(context.text.strip()) if context.text else {}
    error = context.last_rpc_error
    assert error is not None, "Expected RPC error, but call succeeded."
    assert isinstance(error, RpcClientError)
    actual = {"code": error.code, "message": error.message}
    assert (
        actual["code"] == error_code
    ), f"RPC error code mismatch.\nExpected: {error_code}\nActual:   {actual['code']}"
    if expected:
        assert (
            actual == expected
        ), f"RPC error mismatch.\nExpected: {expected}\nActual:   {actual}"


@then("the Telegram API should contain a sendMessage matching")
def step_telegram_api_should_contain_send_message_matching(context):
    expected = json.loads(context.text.strip()) if context.text else {}
    time.sleep(1)
    requests = context.manager.get_http_requests("telegram-api-mock") or []
    assert requests, "No Telegram API call captured."
    for payload in requests:
        actual = {
            "chat_id": str(payload.get("chat_id", "")),
            "text": payload.get("text", ""),
        }
        parse_mode = payload.get("parse_mode")
        if parse_mode:
            actual["parse_mode"] = parse_mode
        if actual == expected:
            return
    raise AssertionError(
        f"No Telegram API call matched expected={expected}. requests={requests}"
    )


@then("the Telegram API should contain no sendMessage")
def step_telegram_api_should_contain_no_send_message(context):
    requests = context.manager.get_http_requests("telegram-api-mock") or []
    assert not requests, f"Expected no Telegram API calls, got {requests}"


@then("the telegram-notifier service rejects the event as invalid payload")
def step_telegram_notifier_rejects_invalid_payload(context):
    _ = context.last_published_event_payload
    requests = context.manager.get_http_requests("telegram-api-mock") or []
    assert not requests, f"Expected no Telegram API calls, got {requests}"


@when("the telegram-notifier service fails to start with the following configuration")
def step_telegram_notifier_fails_to_start_with_config(context):
    config_text = context.text.strip()
    config = yaml.safe_load(config_text) or {}
    context.telegram_notifier_config = config

    proc, config_path = start_telegram_notifier_subprocess(config)
    context.telegram_notifier_config_path = config_path
    time.sleep(5)
    exit_code = proc.poll()
    stderr = (
        proc.stderr.read().decode(errors="replace") if proc.stderr else ""
    ) or "(empty)"
    if exit_code is None:
        proc.terminate()
        proc.wait(timeout=5)
        raise AssertionError(
            "Expected telegram-notifier startup to fail, but process is still running."
        )
    context.telegram_notifier_startup_stderr = stderr
    context.telegram_notifier_process = None


def _startup_error_mentions(context, fragment):
    stderr = context.telegram_notifier_startup_stderr or ""
    lowered = stderr.lower()
    assert fragment in lowered, (
        f"Expected startup error to mention {fragment}.\n" f"stderr:\n{stderr}"
    )


@then("the telegram-notifier service startup error mentions endpoints")
def step_telegram_notifier_startup_error_mentions_endpoints(context):
    _startup_error_mentions(context, "endpoints")


@then("the telegram-notifier service startup error mentions the sentinel state path")
def step_telegram_notifier_startup_error_mentions_sentinel_state_path(context):
    _startup_error_mentions(context, "sentinel state path")


@then("the telegram-notifier service startup error mentions the endpoint key")
def step_telegram_notifier_startup_error_mentions_endpoint_key(context):
    _startup_error_mentions(context, "endpoint key")


@then("the service registry eventually receives a heartbeat with degraded flag true")
def step_registry_eventually_reports_degraded(context):
    amqp_url = _registry_amqp_url(context)
    deadline = time.time() + 20
    last_services = {}
    while time.time() < deadline:
        services = _fetch_registry_services(amqp_url)
        last_services = services
        telegram_service = services.get("telegram-notifier-service", {})
        if any(
            isinstance(instance_data, dict)
            and instance_data.get("status") == "degraded"
            for instance_data in telegram_service.values()
        ):
            return
        time.sleep(1)
    raise AssertionError(
        "Expected telegram-notifier-service to become degraded in service registry. "
        f"Last registry payload: {last_services}"
    )
