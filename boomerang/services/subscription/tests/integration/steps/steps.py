import json
import sqlite3
import time
from pathlib import Path

import yaml
from behave import given, then, when

from boomerang.core.contracts.subscription import CreateSubscriptionRequest
from boomerang.services.subscription.tests.integration.utils import (
    http_request,
    register_identity_session,
    start_subscription_subprocess,
)


def _normalize_actual_for_placeholders(expected, actual):
    if isinstance(expected, dict) and isinstance(actual, dict):
        # Keep only expected keys so scenarios can assert partial payloads.
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
    if hasattr(context, "last_subscription_id"):
        resolved = resolved.replace("[SUB_ID]", context.last_subscription_id)
    if hasattr(context, "last_user_id"):
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


def _sqlite_path_from_context(context):
    config = getattr(context, "subscription_config", None) or {}
    return config.get("app", {}).get("storage", {}).get("sqlite_path")


def _fetch_all_rows(sqlite_path, table_name):
    with sqlite3.connect(sqlite_path) as connection:
        connection.row_factory = sqlite3.Row
        rows = connection.execute(f"SELECT * FROM {table_name}").fetchall()
    return [dict(row) for row in rows]


def _rows_from_context_table(context):
    if context.table is None:
        raise AssertionError("This step requires a Gherkin data table.")
    return [
        {heading: row[heading] for heading in context.table.headings}
        for row in context.table
    ]


def _normalize_scalar(value):
    if value is None:
        return None
    if isinstance(value, str):
        stripped = value.strip()
        if stripped == "null":
            return None
        if stripped.startswith("{") or stripped.startswith("["):
            try:
                return json.loads(stripped)
            except Exception:
                return stripped
        if stripped in {"0", "1"}:
            return int(stripped)
        return stripped
    return value


def _sql_literal(value):
    if isinstance(value, (dict, list)):
        return json.dumps(value, separators=(",", ":"))
    return value


def _normalize_table_rows(rows):
    normalized = []
    for row in rows:
        normalized.append({key: _normalize_scalar(value) for key, value in row.items()})
    return normalized


def _normalize_db_rows_for_expected(expected_rows, actual_rows):
    normalized = []
    for expected, actual in zip(expected_rows, actual_rows):
        normalized_row = {}
        for key, expected_value in expected.items():
            actual_value = actual.get(key)
            if (
                isinstance(expected_value, str)
                and expected_value.startswith("[")
                and expected_value.endswith("]")
            ):
                normalized_row[key] = expected_value
            else:
                normalized_row[key] = actual_value
        normalized.append(normalized_row)
    return normalized


def _extract_auth_code_from_notification_event(context):
    catcher_name = "notification-event-catcher"
    events = context.manager.get_events(catcher_name, wait_for_events=1, timeout=10)
    assert events, "No event published for email.alerting.notification.requested"
    match = None
    for event in events:
        if event.get("event_type") == "email.alerting.notification.requested":
            match = event
    assert (
        match is not None
    ), f"Event email.alerting.notification.requested not found in {events}"
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
    context.subscription_config = config

    sqlite_path = _sqlite_path_from_context(context)
    context.subscription_sqlite_path = sqlite_path
    if sqlite_path:
        db_path = Path(sqlite_path)
        if db_path.parent:
            db_path.parent.mkdir(parents=True, exist_ok=True)
        if db_path.exists():
            db_path.unlink()

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
    access_token = "test-access-token"
    context.last_access_token = access_token
    register_identity_session(context, email, access_token)


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
    # For create_subscription, simulate real RPC usage by passing a Pydantic model
    # instead of a raw dict so delegate expectations (body.delivery, etc.) are met.
    if method_name == "create_subscription" and isinstance(payload, dict):
        body_dict = payload.get("body")
        if isinstance(body_dict, dict):
            payload["body"] = CreateSubscriptionRequest(**body_dict)
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
    resolved_user_id = _resolve_placeholders(user_id, context)
    context.last_user_id = resolved_user_id


@then("the attach_channel_endpoint RPC call succeeds")
def step_attach_channel_endpoint_rpc_success(context):
    if context.last_rpc_error is not None:
        raise AssertionError(
            f"Expected RPC success, got error: {context.last_rpc_error}"
        )


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
    actual = context.last_rpc_result
    normalized_actual = _normalize_actual_for_placeholders(expected, actual)
    assert (
        normalized_actual == expected
    ), f"RPC response mismatch.\nExpected: {expected}\nActual:   {normalized_actual}"


@then("the attach_channel_endpoint request is rejected due to validation error")
def step_attach_channel_endpoint_validation_error(context):
    expected = json.loads(context.text.strip()) if context.text else {}
    error = context.last_rpc_error
    assert error is not None, "Expected RPC validation error, but call succeeded."
    actual = {"code": error.code, "message": error.message}
    assert (
        actual == expected
    ), f"RPC error mismatch.\nExpected: {expected}\nActual:   {actual}"


@when("I wait {seconds:d} seconds")
@when("I wait {seconds:d} second")
def step_wait_seconds(context, seconds):
    _ = context
    time.sleep(seconds)


@then("the request-auth-code response is")
@then("the consume-auth-code response is")
@then("the create-subscriptions response is")
@then("the update-subscription response is")
@then("the delete-subscription response is")
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
    if isinstance(body, dict):
        created = body.get("created")
        if isinstance(created, list) and created:
            first = created[0]
            if isinstance(first, dict):
                subscription_id = first.get("subscription_id")
                if isinstance(subscription_id, str) and subscription_id:
                    context.last_subscription_id = subscription_id
        item = body.get("item")
        if isinstance(item, dict):
            subscription_id = item.get("subscription_id")
            if isinstance(subscription_id, str) and subscription_id:
                context.last_subscription_id = subscription_id


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


@then("the request-auth-code call is rejected with HTTP {status_code:d}")
@then("the consume-auth-code call is rejected with HTTP {status_code:d}")
@then("the list-subscriptions call is rejected with HTTP {status_code:d}")
@then("the create-subscriptions call is rejected with HTTP {status_code:d}")
@then("the update-subscription call is rejected with HTTP {status_code:d}")
@then("the delete-subscription call is rejected with HTTP {status_code:d}")
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
@then("the list-channels response is")
@then("the list-alerts response is")
def step_list_subscriptions_response(context):
    _assert_success_response(context)


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
    values = [
        [_sql_literal(_normalize_scalar(row[col])) for col in columns] for row in rows
    ]

    with sqlite3.connect(sqlite_path) as connection:
        connection.execute("PRAGMA foreign_keys = ON;")
        connection.execute(f"DELETE FROM {table_name}")
        connection.executemany(
            f"INSERT INTO {table_name} ({quoted_columns}) VALUES ({placeholders})",
            values,
        )


@then('the "{table_name}" table should contain')
def step_assert_table_equals(context, table_name):
    sqlite_path = _sqlite_path_from_context(context)
    if not sqlite_path:
        raise AssertionError("Missing app.storage.sqlite_path in test configuration.")

    expected_rows = _normalize_table_rows(_rows_from_context_table(context))
    actual_rows = _normalize_table_rows(_fetch_all_rows(sqlite_path, table_name))

    if len(expected_rows) != len(actual_rows):
        raise AssertionError(
            f"Row count mismatch for {table_name}. "
            f"Expected {len(expected_rows)} rows, got {len(actual_rows)}.\n"
            f"Expected: {expected_rows}\nActual: {actual_rows}"
        )

    normalized_actual = _normalize_db_rows_for_expected(expected_rows, actual_rows)
    expected_signatures = sorted(
        json.dumps(row, sort_keys=True, ensure_ascii=True) for row in expected_rows
    )
    actual_signatures = sorted(
        json.dumps(row, sort_keys=True, ensure_ascii=True) for row in normalized_actual
    )
    assert actual_signatures == expected_signatures, (
        f"Table mismatch for {table_name}.\n"
        f"Expected: {expected_rows}\n"
        f"Actual:   {normalized_actual}"
    )


@then("no account existence information is disclosed in the response")
def step_no_account_existence_disclosed(context):
    status, body = _last_response(context)
    assert status == 200, f"Expected HTTP 200, got {status} body={body}"
    assert body == {"status": "ok"}, f"Unexpected response body: {body}"
