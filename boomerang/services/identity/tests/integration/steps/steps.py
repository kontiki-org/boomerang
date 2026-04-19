import json
import sqlite3
import time
from pathlib import Path

import yaml
from behave import given, then, when

from boomerang.services.identity.tests.integration.utils import (
    http_request,
    start_identity_subprocess,
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
        if "[ISO8601_UTC]" in expected and actual:
            return "[ISO8601_UTC]"
    return actual


def _resolve_placeholders(obj, context):
    if isinstance(obj, dict):
        return {k: _resolve_placeholders(v, context) for k, v in obj.items()}
    if isinstance(obj, list):
        return [_resolve_placeholders(v, context) for v in obj]
    if isinstance(obj, str):
        if obj == "[LAST_CODE]":
            return getattr(context, "last_code", "")
        if obj == "[LAST_ACCESS_TOKEN]":
            return getattr(context, "last_access_token", "")
        return obj
    return obj


def _last_response(context):
    return context.last_http_status, context.last_http_body


def _assert_success_response(context):
    expected = json.loads(context.text.strip()) if context.text else {}
    status, body = _last_response(context)
    assert status == 200, f"Expected HTTP 200, got {status} body={body}"
    normalized_body = _normalize_actual_for_placeholders(expected, body)
    assert (
        normalized_body == expected
    ), f"Response mismatch.\nExpected: {expected}\nActual:   {normalized_body}"


def _sqlite_path_from_context(context):
    config = getattr(context, "identity_config", {}) or {}
    return config.get("app", {}).get("storage", {}).get("sqlite_path")


def _rows_from_context_table(context):
    if not context.table:
        return []
    return [row.as_dict() for row in context.table]


def _normalize_scalar(value):
    return value


def _fetch_all_rows(sqlite_path: str, table_name: str):
    with sqlite3.connect(sqlite_path) as connection:
        connection.execute("PRAGMA foreign_keys = ON;")
        cursor = connection.execute(f"SELECT * FROM {table_name}")
        cols = [d[0] for d in cursor.description]
        return [dict(zip(cols, row)) for row in cursor.fetchall()]


@given("the identity service is running with the following configuration")
def step_identity_running_with_config(context):
    config_text = context.text.strip()
    config = yaml.safe_load(config_text) or {}
    context.identity_config = config
    sqlite_path = _sqlite_path_from_context(context)
    context.identity_sqlite_path = sqlite_path
    if sqlite_path:
        db_path = Path(sqlite_path)
        if db_path.parent:
            db_path.parent.mkdir(parents=True, exist_ok=True)
        if db_path.exists():
            db_path.unlink()

    proc, config_path = start_identity_subprocess(config)
    context.identity_process = proc
    context.identity_config_path = config_path
    time.sleep(5)
    if proc.poll() is not None:
        stderr = (
            proc.stderr.read().decode(errors="replace") if proc.stderr else ""
        ) or "(empty)"
        raise RuntimeError(
            "Identity subprocess exited before step. stderr:\n%s" % stderr
        )


@when("I call {method} on the identity service on {url} with the following request")
def step_call_request_on_identity_service_with_request(context, method, url):
    payload = json.loads(context.text.strip()) if context.text else {}
    headers = payload.get("headers")
    body = payload.get("payload")
    headers = _resolve_placeholders(headers, context)
    body = _resolve_placeholders(body, context)
    status, resp_body = http_request(method, url, payload=body, headers=headers)
    context.last_http_status = status
    context.last_http_body = resp_body


@when("I wait {seconds:d} seconds")
@when("I wait {seconds:d} second")
def step_wait_seconds(context, seconds):
    _ = context
    time.sleep(seconds)


@then("the request-auth-code response is")
@then("the consume-auth-code response is")
def step_success_response(context):
    _assert_success_response(context)


@then("the request-auth-code call is rejected with HTTP {status_code:d}")
@then("the consume-auth-code call is rejected with HTTP {status_code:d}")
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


@then('a "{event_type}" event is published')
@then('an "{event_type}" event is published')
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
    if event_type == "email.alerting.notification.requested":
        auth_code = (
            actual_payload.get("message", {})
            .get("context", {})
            .get("data", {})
            .get("auth_code", "")
        )
        if isinstance(auth_code, str) and auth_code:
            context.last_code = auth_code
    context.manager.clean_events(catcher_name)


@given('the "{table_name}" table contains')
def step_seed_table(context, table_name):
    sqlite_path = _sqlite_path_from_context(context)
    if not sqlite_path:
        raise AssertionError("Missing app.storage.sqlite_path in test configuration.")
    rows = _rows_from_context_table(context)
    if not rows:
        return

    columns = context.table.headings
    placeholders = ", ".join("?" for _ in columns)
    quoted_columns = ", ".join(columns)
    values = [[_normalize_scalar(row[col]) for col in columns] for row in rows]

    with sqlite3.connect(sqlite_path) as connection:
        connection.execute("PRAGMA foreign_keys = ON;")
        connection.execute(f"DELETE FROM {table_name}")
        connection.executemany(
            f"INSERT INTO {table_name} ({quoted_columns}) VALUES ({placeholders})",
            values,
        )


@then('the "{table_name}" table should contain')
def step_assert_table_contains(context, table_name):
    sqlite_path = _sqlite_path_from_context(context)
    if not sqlite_path:
        raise AssertionError("Missing app.storage.sqlite_path in test configuration.")
    expected_rows = _rows_from_context_table(context)
    actual_rows = _fetch_all_rows(sqlite_path, table_name)
    assert len(actual_rows) == len(expected_rows), (
        f"Row count mismatch for {table_name}. "
        f"Expected {len(expected_rows)} rows, got {len(actual_rows)}"
    )
