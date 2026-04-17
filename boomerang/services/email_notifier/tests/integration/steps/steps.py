import json
import sqlite3
import time
from pathlib import Path

import yaml
from behave import given, then, when
from pydantic import ValidationError as PydanticValidationError

from boomerang.core.contracts.notification import NotificationRequest
from boomerang.services.email_notifier.tests.integration import mailhog
from boomerang.services.email_notifier.tests.integration.utils import (
    http_request,
    start_email_notifier_subprocess,
)
from boomerang.services.subscription.tests.integration.utils import (
    register_identity_session,
)


def _last_response(context):
    return context.last_http_status, context.last_http_body


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


def _assert_success_response(context):
    expected = json.loads(context.text.strip()) if context.text else {}
    status, body = _last_response(context)
    assert status == 200, f"Expected HTTP 200, got {status} body={body}"
    normalized_body = _normalize_actual_for_placeholders(expected, body)
    assert (
        normalized_body == expected
    ), f"Response mismatch.\nExpected: {expected}\nActual:   {normalized_body}"


def _sqlite_path_from_context(context):
    config = getattr(context, "email_notifier_config", {}) or {}
    return config.get("app", {}).get("storage", {}).get("sqlite_path")


def _fetch_all_rows(sqlite_path: str, table_name: str):
    with sqlite3.connect(sqlite_path) as connection:
        connection.execute("PRAGMA foreign_keys = ON;")
        cursor = connection.execute(f"SELECT * FROM {table_name}")
        cols = [d[0] for d in cursor.description]
        return [dict(zip(cols, row)) for row in cursor.fetchall()]


def _rows_from_context_table(context):
    if context.table is None:
        raise AssertionError("This step requires a Gherkin data table.")
    return [row.as_dict() for row in context.table]


def _assert_event_published(context, event_type: str):
    expected_payload = json.loads(context.text.strip()) if context.text else {}
    catcher_name = "notification-outcome-catcher"
    events = context.manager.get_events(catcher_name, wait_for_events=1, timeout=10)
    assert events, f"No event published for {event_type}"
    match = None
    for event in events:
        if event.get("event_type") == event_type:
            match = event
            break
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


@given("the email-notifier service is running with the following configuration")
def step_email_notifier_running_with_config(context):
    config_text = context.text.strip()
    config = yaml.safe_load(config_text) or {}
    context.email_notifier_config = config
    sqlite_path = _sqlite_path_from_context(context)
    context.email_notifier_sqlite_path = sqlite_path
    if sqlite_path:
        db_path = Path(sqlite_path)
        if db_path.parent:
            db_path.parent.mkdir(parents=True, exist_ok=True)
        if db_path.exists():
            db_path.unlink()

    proc, config_path = start_email_notifier_subprocess(config)
    context.email_notifier_process = proc
    context.email_notifier_config_path = config_path
    time.sleep(5)
    if proc.poll() is not None:
        stderr = (
            proc.stderr.read().decode(errors="replace") if proc.stderr else ""
        ) or "(empty)"
        raise RuntimeError(
            "EmailNotifier subprocess exited before step. stderr:\n%s" % stderr
        )


@given('I am authenticated as "{email}"')
def step_i_am_authenticated_as(context, email):
    access_token = "test-access-token"
    context.last_access_token = access_token
    register_identity_session(context, email, access_token)


@when('an "{event_type}" event is published with payload')
def step_publish_event_with_payload(context, event_type):
    payload = json.loads(context.text.strip()) if context.text else {}
    assert (
        event_type == "alerting.notification.requested"
    ), f"Unsupported event type for this step: {event_type}"
    mailhog.purge_messages()
    context.last_published_event_type = event_type
    context.last_published_event_payload = payload
    request_payload = NotificationRequest.model_validate(payload)
    context.runner.call(
        "notification-publisher",
        "publish_notification_requested",
        payload=request_payload,
    )
    time.sleep(1)


@when(
    "I call {method} on the email-notifier service on {url} with the following request"
)
def step_call_request_on_email_notifier_service_with_request(context, method, url):
    payload = json.loads(context.text.strip()) if context.text else {}
    headers = payload.get("headers")
    body = payload.get("payload")
    # inject Authorization header when we have a last access token
    token = getattr(context, "last_access_token", None)
    if token:
        headers = headers or {}
        headers.setdefault("Authorization", f"Bearer {token}")
    status, resp_body = http_request(method, url, payload=body, headers=headers)
    context.last_http_status = status
    context.last_http_body = resp_body


@then("the create-email-endpoint response is")
def step_create_email_endpoint_success_response(context):
    _assert_success_response(context)


@then("the list-email-endpoints response is")
def step_list_email_endpoints_success_response(context):
    _assert_success_response(context)


@then("the get-email-endpoint response is")
def step_get_email_endpoint_success_response(context):
    _assert_success_response(context)


@then("the delete-email-endpoint response is")
def step_delete_email_endpoint_success_response(context):
    _assert_success_response(context)


@then("MailHog should contain an email matching")
def step_mailhog_should_contain_email_matching(context):
    expected = json.loads(context.text.strip()) if context.text else {}
    expected_to = expected.get("to", [])
    expected_subject = expected.get("subject", "")
    expected_from = expected.get("from", "")
    expected_body_contains = expected.get("body_contains", [])

    messages = mailhog.list_messages()
    assert messages, "No email found in MailHog."

    for message in messages:
        content = message.get("Content", {})
        headers = content.get("Headers", {})
        raw_body = content.get("Body", "")
        to_values = headers.get("To", [])
        from_values = headers.get("From", [])
        subject_values = headers.get("Subject", [])

        actual_to = [value.strip() for value in to_values if isinstance(value, str)]
        actual_from = from_values[0].strip() if from_values else ""
        actual_subject = subject_values[0].strip() if subject_values else ""

        if expected_to and actual_to != expected_to:
            continue
        if expected_from and actual_from != expected_from:
            continue
        if expected_subject and actual_subject != expected_subject:
            continue
        if any(fragment not in raw_body for fragment in expected_body_contains):
            continue
        return

    raise AssertionError(
        f"No MailHog message matched expected payload={expected}. Messages={messages}"
    )


@then('a "{event_type}" event is published')
def step_event_is_published(context, event_type):
    _assert_event_published(context, event_type)


@then("the email-notifier service ignores the event")
def step_email_notifier_ignores_event(context):
    messages = mailhog.list_messages()
    assert not messages, f"Expected no email in MailHog, got {messages}"


@then("the email-notifier service rejects the event as invalid payload")
def step_email_notifier_rejects_invalid_payload(context):
    payload = getattr(context, "last_published_event_payload", None) or {}
    try:
        NotificationRequest.model_validate(payload)
    except PydanticValidationError:
        pass
    messages = mailhog.list_messages()
    assert not messages, f"Expected no email in MailHog, got {messages}"


@then("the create-email-endpoint call is rejected with HTTP {status_code:d}")
def step_create_email_endpoint_rejected_response(context, status_code):
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


@then("the get-email-endpoint call is rejected with HTTP {status_code:d}")
def step_get_email_endpoint_rejected_response(context, status_code):
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


@then('the "email_endpoints" table should contain')
def step_email_endpoints_table_should_contain(context):
    sqlite_path = _sqlite_path_from_context(context)
    assert sqlite_path, "No sqlite path configured for email-notifier tests."
    expected_rows = _rows_from_context_table(context)
    actual_rows = _fetch_all_rows(sqlite_path, "email_endpoints")

    # For each expected row, ensure there is at least one matching actual row.
    for expected in expected_rows:
        matched = False
        for actual in actual_rows:
            ok = True
            for key, expected_value in expected.items():
                actual_value = actual.get(key)
                if (
                    isinstance(expected_value, str)
                    and expected_value.startswith("[")
                    and expected_value.endswith("]")
                ):
                    # Placeholder: accept any actual value.
                    continue
                if actual_value != expected_value:
                    ok = False
                    break
            if ok:
                matched = True
                break
        assert (
            matched
        ), f"Expected row not found in email_endpoints: {expected}\nActual rows: {actual_rows}"
