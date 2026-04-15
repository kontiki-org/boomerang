import copy
import json
import time

import yaml
from behave import given, then, when

from boomerang.services.subscription.tests.integration.utils import (
    http_request,
    start_subscription_subprocess,
)


def _normalize_actual_for_placeholders(expected, actual):
    if isinstance(expected, dict) and isinstance(actual, dict):
        normalized = copy.deepcopy(actual)
        for key, expected_value in expected.items():
            if key in normalized:
                normalized[key] = _normalize_actual_for_placeholders(
                    expected_value, normalized[key]
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


def _last_response(context):
    if not hasattr(context, "last_http_status"):
        raise AssertionError("No HTTP response recorded. Call a When step first.")
    return context.last_http_status, context.last_http_body


def _resolve_placeholders(text, context):
    resolved = text
    if hasattr(context, "last_code"):
        resolved = resolved.replace("[LAST_CODE]", context.last_code)
    if hasattr(context, "last_access_token"):
        resolved = resolved.replace("[LAST_ACCESS_TOKEN]", context.last_access_token)
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


def _extract_auth_code_from_notification_event(context):
    catcher_name = "notification-event-catcher"
    events = context.manager.get_events(catcher_name, wait_for_events=1, timeout=10)
    assert events, "No event published for alerting.notification.requested"
    match = None
    for event in events:
        if event.get("event_type") == "alerting.notification.requested":
            match = event
    assert (
        match is not None
    ), f"Event alerting.notification.requested not found in {events}"
    payload = match.get("payload", {})
    if hasattr(payload, "model_dump"):
        payload = payload.model_dump()
    auth_code = (
        payload.get("message", {})
        .get("context", {})
        .get("data", {})
        .get("auth_code", "")
    )
    assert (
        isinstance(auth_code, str) and auth_code
    ), f"No auth_code in payload: {payload}"
    context.manager.clean_events(catcher_name)
    return auth_code


@given("the subscription service is running with the following configuration")
def step_subscription_running_with_config(context):
    config_text = context.text.strip()
    config = yaml.safe_load(config_text) or {}

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


@given('I am authenticated as "{email}"')
def step_i_am_authenticated_as(context, email):
    status, body = http_request(
        "POST",
        "http://127.0.0.1:8000/auth/request-auth-code",
        payload={"email": email},
    )
    assert status == 200, f"Expected HTTP 200, got {status} body={body}"
    assert body == {"status": "ok"}, f"Unexpected response body: {body}"
    context.last_code = _extract_auth_code_from_notification_event(context)

    status, body = http_request(
        "POST",
        "http://127.0.0.1:8000/auth/consume-auth-code",
        payload={"code": context.last_code},
    )
    assert status == 200, f"Expected HTTP 200, got {status} body={body}"
    assert body.get("status") == "ok", f"Unexpected response body: {body}"
    assert body.get("token_type") == "Bearer", f"Unexpected response body: {body}"
    access_token = body.get("access_token")
    assert (
        isinstance(access_token, str) and access_token
    ), f"Expected non-empty access_token, got {body}"
    context.last_access_token = access_token


@when("I call {method} on the subscription service on {url} with the following request")
def step_call_request_on_subscription_service_with_request(context, method, url):
    headers, payload = _parse_request_block(context)
    status, body = http_request(method, url, payload=payload, headers=headers)
    context.last_http_status = status
    context.last_http_body = body


@when("I wait {seconds:d} seconds")
@when("I wait {seconds:d} second")
def step_wait_seconds(context, seconds):
    _ = context
    time.sleep(seconds)


@then("the request-auth-code response is")
@then("the consume-auth-code response is")
def step_success_response(context):
    _assert_success_response(context)


def _assert_success_response(context):
    expected = json.loads(context.text.strip()) if context.text else {}
    status, body = _last_response(context)
    assert status == 200, f"Expected HTTP 200, got {status} body={body}"
    normalized_body = _normalize_actual_for_placeholders(expected, body)
    assert (
        normalized_body == expected
    ), f"Response mismatch.\nExpected: {expected}\nActual:   {normalized_body}"
    access_token = body.get("access_token")
    if isinstance(access_token, str) and access_token:
        context.last_access_token = access_token


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
    actual_payload = match.get("payload", {})
    if hasattr(actual_payload, "model_dump"):
        actual_payload = actual_payload.model_dump()

    normalized_payload = _normalize_actual_for_placeholders(
        expected_payload, actual_payload
    )
    assert normalized_payload == expected_payload, (
        "Event payload mismatch.\n"
        f"Expected: {expected_payload}\n"
        f"Actual:   {normalized_payload}"
    )
    if event_type == "alerting.notification.requested":
        auth_code = (
            actual_payload.get("message", {})
            .get("context", {})
            .get("data", {})
            .get("auth_code", "")
        )
        if isinstance(auth_code, str) and auth_code:
            context.last_code = auth_code
    context.manager.clean_events(catcher_name)


@then("the request-auth-code call is rejected with HTTP {status_code:d}")
@then("the consume-auth-code call is rejected with HTTP {status_code:d}")
@then("the list-subscriptions call is rejected with HTTP {status_code:d}")
def step_rejected_response(context, status_code):
    status, body = _last_response(context)
    assert (
        status == status_code
    ), f"Expected HTTP {status_code}, got {status} body={body}"
    if context.text and context.text.strip():
        expected = json.loads(context.text.strip())
        normalized_body = _normalize_actual_for_placeholders(expected, body)
        assert (
            normalized_body == expected
        ), f"Error body mismatch.\nExpected: {expected}\nActual:   {normalized_body}"


@then("the list-subscriptions response is")
def step_list_subscriptions_response(context):
    _assert_success_response(context)


@then("no account existence information is disclosed in the response")
def step_no_account_existence_disclosed(context):
    status, body = _last_response(context)
    assert status == 200, f"Expected HTTP 200, got {status} body={body}"
    assert body == {"status": "ok"}, f"Unexpected response body: {body}"
