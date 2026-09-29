import json
import time

import yaml
from behave import given, then, when
from kontiki.messaging import RpcClientError
from pydantic import BaseModel

from boomerang.services.subscription.tests.integration.utils import (
    configured_notification_channels,
    email_notifier_config_for_subscription_tests,
    http_request,
    start_email_notifier_subprocess,
    start_subscription_subprocess,
)


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
        if "[CODE]" in expected and actual:
            return "[CODE]"
        if "[ISO8601_UTC]" in expected:
            return "[ISO8601_UTC]"

    return actual


def _as_jsonable(value):
    if isinstance(value, BaseModel):
        return value.model_dump(mode="json")
    return value


def _resolve_placeholders(text, context):
    resolved = text
    if context.last_code is not None:
        resolved = resolved.replace("[LAST_CODE]", context.last_code)
    if context.last_access_token is not None:
        resolved = resolved.replace("[LAST_ACCESS_TOKEN]", context.last_access_token)
    if context.last_subscription_id is not None:
        resolved = resolved.replace("[SUB_ID]", context.last_subscription_id)
    if context.last_user_id is not None:
        resolved = resolved.replace("[USER_ID]", context.last_user_id)
    return resolved


def _parse_request_block(context):
    if not context.text or not context.text.strip():
        return None, None
    request_text = _resolve_placeholders(context.text.strip(), context)
    request_data = json.loads(request_text)
    if not isinstance(request_data, dict):
        raise AssertionError("Request block must be a JSON object.")
    headers = request_data.get("headers")
    payload = request_data.get("payload")
    if headers is not None and not isinstance(headers, dict):
        raise AssertionError("'headers' must be a JSON object when provided.")
    return headers, payload


@given("the subscription service is running with the following configuration")
def step_subscription_running_with_config(context):
    config_text = context.text.strip()
    config = yaml.safe_load(config_text) or {}
    context.subscription_config = config

    if "email-notifier-service" in configured_notification_channels(config):
        email_config = email_notifier_config_for_subscription_tests()
        email_proc, email_config_path = start_email_notifier_subprocess(email_config)
        context.email_notifier_process = email_proc
        context.email_notifier_config_path = email_config_path
        time.sleep(5)
        if email_proc.poll() is not None:
            stderr = (
                email_proc.stderr.read().decode(errors="replace")
                if email_proc.stderr
                else ""
            ) or "(empty)"
            raise RuntimeError(
                "Email notifier subprocess exited before step. stderr:\n%s" % stderr
            )

    proc, config_path = start_subscription_subprocess(config)
    context.subscription_process = proc
    context.subscription_config_path = config_path
    time.sleep(5)
    if proc.poll() is not None:
        stderr = (
            proc.stderr.read().decode(errors="replace") if proc.stderr else ""
        ) or "(empty)"
        raise RuntimeError(
            "Subscription subprocess exited before step. stderr:\n%s" % stderr
        )


@when("I call {method} on the subscription service on {url} with the following request")
def step_call_request_on_subscription_service_with_request(context, method, url):
    headers, payload = _parse_request_block(context)
    resolved_url = _resolve_placeholders(url, context)
    status, body = http_request(method, resolved_url, payload=payload, headers=headers)
    context.last_http_status = status
    context.last_http_body = body


@when(
    "I call the RPC {method_name} on the subscription service with the following arguments"
)
def step_call_rpc_on_subscription_service(context, method_name):
    payload_text = _resolve_placeholders(context.text.strip(), context)
    payload = json.loads(payload_text) if payload_text else {}
    extra_headers = None
    if isinstance(payload, dict) and "headers" in payload:
        extra_headers = payload.pop("headers")
    context.last_rpc_error = None
    try:
        context.last_rpc_result = context.runner.call(
            "subscription-service",
            method_name,
            extra_headers=extra_headers,
            **payload,
        )
    except Exception as exc:
        context.last_rpc_result = None
        context.last_rpc_error = exc


@given('I have resolved the subscription user id as "{user_id}"')
@then('I have resolved the subscription user id as "{user_id}"')
def step_resolve_subscription_user_id(context, user_id):
    context.last_user_id = _resolve_placeholders(user_id, context)


@then("the RPC call succeeds")
def step_rpc_call_succeeds(context):
    if context.last_rpc_error is not None:
        raise AssertionError(
            f"Expected RPC success, got error: {context.last_rpc_error}"
        )


@then("the RPC response is")
def step_rpc_response_is(context):
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


@then("the RPC call fails with a {error_code}")
def step_rpc_call_fails_with_error_code(context, error_code):
    expected = json.loads(context.text.strip()) if context.text else {}
    error = context.last_rpc_error
    assert error is not None, "Expected RPC error, but call succeeded."
    assert isinstance(
        error, RpcClientError
    ), f"Expected RpcClientError, got {type(error)}: {error}"
    actual = {"code": error.code, "message": error.message}
    assert (
        actual["code"] == error_code
    ), f"RPC error code mismatch.\nExpected: {error_code}\nActual:   {actual['code']}"
    if expected:
        assert (
            actual == expected
        ), f"RPC error mismatch.\nExpected: {expected}\nActual:   {actual}"


@then("the RPC request is rejected due to validation error")
def step_rpc_validation_error(context):
    expected = json.loads(context.text.strip()) if context.text else {}
    error = context.last_rpc_error
    assert error is not None, "Expected RPC validation error, but call succeeded."
    assert isinstance(
        error, RpcClientError
    ), f"Expected RpcClientError, got {type(error)}: {error}"
    actual = {"code": error.code, "message": error.message}
    assert (
        actual == expected
    ), f"RPC error mismatch.\nExpected: {expected}\nActual:   {actual}"


@when("I wait {seconds:d} seconds")
@when("I wait {seconds:d} second")
def step_wait_seconds(context, seconds):
    _ = context
    time.sleep(seconds)


@then("the HTTP response status is {status:d}")
def step_http_response_status(context, status):
    assert context.last_http_status == status, "Expected HTTP %s, got %s body=%s" % (
        status,
        context.last_http_status,
        context.last_http_body,
    )


@then("the HTTP response is")
def step_http_response_is(context):
    expected = json.loads(context.text.strip()) if context.text else {}
    actual = context.last_http_body
    assert actual == expected, "Expected %s, got %s" % (expected, actual)


@then('a "{event_type}" event is published')
def step_event_is_published(context, event_type):
    expected_payload = json.loads(context.text.strip()) if context.text else {}
    catcher_name = "notification-event-catcher"
    events = context.manager.get_events(catcher_name, wait_for_events=1, timeout=10)
    assert events, f"No event published for {event_type}"
    match = None
    for event in events:
        if event.get("event_type") == event_type:
            match = event
    assert match is not None, f"Event {event_type} not found in {events}"
    actual_payload = _as_jsonable(match.get("payload", {}))

    normalized_payload = _normalize_actual_for_placeholders(
        expected_payload, actual_payload
    )
    assert normalized_payload == expected_payload, (
        "Event payload mismatch.\n"
        f"Expected: {expected_payload}\n"
        f"Actual:   {normalized_payload}"
    )
    context.manager.clean_events(catcher_name)


@when("the subscription service fails to start with the following configuration")
def step_subscription_fails_to_start_with_config(context):
    config_text = context.text.strip()
    config = yaml.safe_load(config_text) or {}
    context.subscription_config = config

    proc, config_path = start_subscription_subprocess(config)
    context.subscription_config_path = config_path
    time.sleep(5)
    exit_code = proc.poll()
    stderr = (
        proc.stderr.read().decode(errors="replace") if proc.stderr else ""
    ) or "(empty)"
    if exit_code is None:
        proc.terminate()
        proc.wait(timeout=5)
        raise AssertionError(
            "Expected subscription service startup to fail, but process is still running."
        )
    context.subscription_startup_stderr = stderr
    context.subscription_process = None


@then("the subscription service startup error mentions subscriptions")
def step_subscription_startup_error_mentions_subscriptions(context):
    stderr = context.subscription_startup_stderr or ""
    lowered = stderr.lower()
    assert "subscriptions" in lowered, (
        "Expected startup error to mention subscriptions.\n" f"stderr:\n{stderr}"
    )
