import copy
import json
import time

import yaml
from behave import given, then, when

from boomerang.services.subscription.tests.integration.utils import (
    http_request,
    start_subscription_subprocess
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
        if "[TOKEN]" in expected:
            token_value = actual
            if "token=" in actual:
                token_value = actual.split("token=", 1)[1].split("&", 1)[0]
            if token_value:
                return actual.replace(token_value, "[TOKEN]", 1)
        if "[ISO8601_UTC]" in expected:
            return "[ISO8601_UTC]"

    return actual


def _last_response(context):
    if not hasattr(context, "last_http_status"):
        raise AssertionError("No HTTP response recorded. Call a When step first.")
    return context.last_http_status, context.last_http_body


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


@when(
    "I call request-magic-link on the subscription service on {url} with the following payload"
)
def step_call_request_magic_link(context, url):
    payload = json.loads(context.text.strip())
    status, body = http_request(
        "POST",
        f"{url}/auth/request-magic-link",
        payload=payload,
    )
    context.last_http_status = status
    context.last_http_body = body


@when("I wait {seconds:d} seconds")
@when("I wait {seconds:d} second")
def step_wait_seconds(context, seconds):
    _ = context
    time.sleep(seconds)


@then("the request-magic-link response is")
def step_request_magic_link_response(context):
    expected = json.loads(context.text.strip()) if context.text else {}
    status, body = _last_response(context)
    assert status == 200, f"Expected HTTP 200, got {status} body={body}"
    normalized_body = _normalize_actual_for_placeholders(expected, body)
    assert normalized_body == expected, (
        f"Response mismatch.\nExpected: {expected}\nActual:   {normalized_body}"
    )


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
    normalized_payload = _normalize_actual_for_placeholders(
        expected_payload, match.get("payload", {})
    )
    assert normalized_payload == expected_payload, (
        "Event payload mismatch.\n"
        f"Expected: {expected_payload}\n"
        f"Actual:   {normalized_payload}"
    )
    context.manager.clean_events(catcher_name)


@then("the request-magic-link call is rejected with HTTP {status_code:d}")
def step_request_magic_link_rejected(context, status_code):
    status, body = _last_response(context)
    assert status == status_code, f"Expected HTTP {status_code}, got {status} body={body}"
    if context.text and context.text.strip():
        expected = json.loads(context.text.strip())
        normalized_body = _normalize_actual_for_placeholders(expected, body)
        assert normalized_body == expected, (
            f"Error body mismatch.\nExpected: {expected}\nActual:   {normalized_body}"
        )


@then("no account existence information is disclosed in the response")
def step_no_account_existence_disclosed(context):
    status, body = _last_response(context)
    assert status == 200, f"Expected HTTP 200, got {status} body={body}"
    assert body == {"status": "ok"}, f"Unexpected response body: {body}"
