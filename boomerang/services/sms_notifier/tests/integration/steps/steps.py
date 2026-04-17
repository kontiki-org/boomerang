import json
import sqlite3
import time
from datetime import datetime, timezone
from pathlib import Path

import yaml
from behave import given, then, when

from boomerang.core.contracts.notification import NotificationRequest
from boomerang.services.sms_notifier.tests.integration.utils import (
    http_request,
    start_sms_notifier_subprocess,
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
    config = getattr(context, "sms_notifier_config", {}) or {}
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


def _insert_rows(sqlite_path: str, table_name: str, rows: list[dict]) -> None:
    if not rows:
        return
    prepared_rows = []
    for row in rows:
        prepared = dict(row)
        if table_name == "sms_endpoints":
            now_iso = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
            prepared.setdefault("created_at", now_iso)
            prepared.setdefault("updated_at", now_iso)
        prepared_rows.append(prepared)

    columns = list(prepared_rows[0].keys())
    placeholders = ", ".join(["?"] * len(columns))
    sql = (
        f"INSERT OR REPLACE INTO {table_name} "
        f"({', '.join(columns)}) VALUES ({placeholders})"
    )
    with sqlite3.connect(sqlite_path) as connection:
        connection.execute("PRAGMA foreign_keys = ON;")
        for row in prepared_rows:
            values = [row.get(col) for col in columns]
            connection.execute(sql, values)
        connection.commit()


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


@given("the sms-notifier service is running with the following configuration")
def step_sms_notifier_running_with_config(context):
    config_text = context.text.strip()
    config = yaml.safe_load(config_text) or {}
    context.sms_notifier_config = config
    sqlite_path = _sqlite_path_from_context(context)
    context.sms_notifier_sqlite_path = sqlite_path
    if sqlite_path:
        db_path = Path(sqlite_path)
        if db_path.parent:
            db_path.parent.mkdir(parents=True, exist_ok=True)
        if db_path.exists():
            db_path.unlink()

    proc, config_path = start_sms_notifier_subprocess(config)
    context.sms_notifier_process = proc
    context.sms_notifier_config_path = config_path
    time.sleep(5)
    if proc.poll() is not None:
        stderr = (
            proc.stderr.read().decode(errors="replace") if proc.stderr else ""
        ) or "(empty)"
        raise RuntimeError(
            "SmsNotifier subprocess exited before step. stderr:\n%s" % stderr
        )


@given('I am authenticated as "{email}"')
def step_i_am_authenticated_as(context, email):
    access_token = "test-access-token"
    context.last_access_token = access_token
    register_identity_session(context, email, access_token)


@given('the "sms_endpoints" table contains')
def step_given_sms_endpoints_table_contains(context):
    sqlite_path = _sqlite_path_from_context(context)
    assert sqlite_path, "No sqlite path configured for sms-notifier tests."
    rows = _rows_from_context_table(context)
    _insert_rows(sqlite_path, "sms_endpoints", rows)


@given("the sms provider will respond with")
def step_sms_provider_will_respond_with(context):
    response = json.loads(context.text.strip()) if context.text else {}
    context.manager.add_http_response("sms-provider-service", response)


@given("the sms provider will respond with HTTP {status_code:d}")
def step_sms_provider_will_respond_with_http_status(context, status_code):
    body = json.loads(context.text.strip()) if context.text else {}
    context.manager.add_http_response("sms-provider-service", (status_code, body))


@when("I call {method} on the sms-notifier service on {url} with the following request")
def step_call_request_on_sms_notifier_service_with_request(context, method, url):
    payload = json.loads(context.text.strip()) if context.text else {}
    headers = payload.get("headers")
    body = payload.get("payload")
    token = getattr(context, "last_access_token", None)
    if token:
        headers = headers or {}
        headers.setdefault("Authorization", f"Bearer {token}")
    status, resp_body = http_request(method, url, payload=body, headers=headers)
    context.last_http_status = status
    context.last_http_body = resp_body


@when('an "{event_type}" event is published with payload')
def step_publish_event_with_payload(context, event_type):
    payload = json.loads(context.text.strip()) if context.text else {}
    context.manager.clean_http_requests("sms-provider-service")
    context.last_published_event_payload = payload
    request_payload = NotificationRequest.model_validate(payload)
    context.runner.call(
        "notification-publisher",
        "publish_event",
        event_type=event_type,
        payload=request_payload,
    )
    time.sleep(1)


@then("the create-sms-endpoint response is")
def step_create_sms_endpoint_success_response(context):
    _assert_success_response(context)


@then("the list-sms-endpoints response is")
def step_list_sms_endpoints_success_response(context):
    _assert_success_response(context)


@then("the get-sms-endpoint response is")
def step_get_sms_endpoint_success_response(context):
    _assert_success_response(context)


@then("the delete-sms-endpoint response is")
def step_delete_sms_endpoint_success_response(context):
    _assert_success_response(context)


@then("the sms provider should contain a message matching")
def step_sms_provider_should_contain_message_matching(context):
    expected = json.loads(context.text.strip()) if context.text else {}
    expected_to = expected.get("to", "")
    expected_body_contains = expected.get("body_contains", [])
    time.sleep(1)
    requests = context.manager.get_http_requests("sms-provider-service") or []
    assert requests, "No SMS provider call captured."
    for payload in requests:
        actual_to = payload.get("to", "")
        actual_body = payload.get("body", "")
        if expected_to and actual_to != expected_to:
            continue
        if any(fragment not in actual_body for fragment in expected_body_contains):
            continue
        return
    raise AssertionError(
        f"No SMS provider call matched expected={expected}. requests={requests}"
    )


@then("the create-sms-endpoint call is rejected with HTTP {status_code:d}")
def step_create_sms_endpoint_rejected_response(context, status_code):
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


@then("the get-sms-endpoint call is rejected with HTTP {status_code:d}")
def step_get_sms_endpoint_rejected_response(context, status_code):
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


@then('a "{event_type}" event is published')
def step_event_is_published(context, event_type):
    _assert_event_published(context, event_type)


@then("the sms-notifier service ignores the event")
def step_sms_notifier_ignores_event(context):
    requests = context.manager.get_http_requests("sms-provider-service") or []
    assert not requests, f"Expected no SMS provider calls, got {requests}"


@then("the sms-notifier service rejects the event as invalid payload")
def step_sms_notifier_rejects_invalid_payload(context):
    _ = context


@then('the "sms_endpoints" table should contain')
def step_sms_endpoints_table_should_contain(context):
    sqlite_path = _sqlite_path_from_context(context)
    assert sqlite_path, "No sqlite path configured for sms-notifier tests."
    expected_rows = _rows_from_context_table(context)
    actual_rows = _fetch_all_rows(sqlite_path, "sms_endpoints")

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
                    continue
                if actual_value != expected_value:
                    ok = False
                    break
            if ok:
                matched = True
                break
        assert (
            matched
        ), f"Expected row not found in sms_endpoints: {expected}\nActual rows: {actual_rows}"

