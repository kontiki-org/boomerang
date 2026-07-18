import asyncio
import json
import sqlite3
import time
from datetime import datetime, timezone
from pathlib import Path

import yaml
from behave import given, then, when
from kontiki.messaging import Messenger
from kontiki.registry.client.proxy import ServiceRegistryProxy

from boomerang.core.contracts.notification.message import NotificationRequest
from boomerang.core.contracts.notification.endpoint import CreateEndpointRequest
from boomerang.services.email_notifier.tests.integration import mailhog
from boomerang.services.email_notifier.tests.integration.utils import (
    http_request,
    start_email_notifier_subprocess,
)
from boomerang.services.identity.database.database import Database as IdentityDatabase
from boomerang.services.subscription.tests.integration.utils import (
    register_identity_session,
)


def _last_response(context):
    return context.last_http_status, context.last_http_body


def _resolve_placeholders(value, context):
    if not isinstance(value, str):
        return value

    replacements = {
        "[USER_ID]": getattr(context, "last_user_id", None),
        "[LAST_ACCESS_TOKEN]": getattr(context, "last_access_token", None),
    }
    resolved = value
    for placeholder, actual in replacements.items():
        if placeholder in resolved and isinstance(actual, str):
            resolved = resolved.replace(placeholder, actual)
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


def _insert_rows(sqlite_path: str, table_name: str, rows: list[dict]) -> None:
    if not rows:
        return
    prepared_rows = []
    for row in rows:
        prepared = dict(row)
        if table_name == "email_endpoints":
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


def _registry_amqp_url(context) -> str:
    config = getattr(context, "email_notifier_config", {}) or {}
    return (
        config.get("kontiki", {}).get("amqp", {}).get("url")
        or "amqp://guest:guest@localhost/"
    )


def _fetch_registry_services(amqp_url: str) -> dict:
    async def _fetch():
        async with Messenger(amqp_url=amqp_url, standalone=True) as messenger:
            proxy = ServiceRegistryProxy(messenger)
            return await proxy.get_services()

    return asyncio.run(_fetch())


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


@given('I have resolved the identity user id for "{email}" as "{user_id}"')
def step_resolve_identity_user_id(context, email, user_id):
    resolved_user_id = IdentityDatabase.build_user_id(email.strip().lower())
    context.last_user_id = resolved_user_id
    expected_user_id = _resolve_placeholders(user_id, context)
    assert resolved_user_id == expected_user_id, (
        f"Resolved user_id mismatch. expected={expected_user_id} "
        f"actual={resolved_user_id}"
    )


@given('the "email_endpoints" table contains')
def step_given_email_endpoints_table_contains(context):
    sqlite_path = _sqlite_path_from_context(context)
    assert sqlite_path, "No sqlite path configured for email-notifier tests."
    rows = _rows_from_context_table(context)
    _insert_rows(sqlite_path, "email_endpoints", rows)


@when('an "{event_type}" event is published with payload')
def step_publish_event_with_payload(context, event_type):
    payload = json.loads(context.text.strip()) if context.text else {}
    mailhog.purge_messages()
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


@when(
    "I call the RPC {method_name} on the email-notifier service with the following arguments"
)
def step_call_rpc_on_email_notifier_service(context, method_name):
    payload_text = _resolve_placeholders(context.text.strip(), context)
    payload = json.loads(payload_text) if payload_text else {}
    if isinstance(payload, dict) and method_name == "create_endpoint":
        body_dict = payload.get("body")
        if isinstance(body_dict, dict):
            payload["body"] = CreateEndpointRequest(**body_dict)
    extra_headers = None
    if isinstance(payload, dict) and "headers" in payload:
        extra_headers = payload.pop("headers")
    context.last_rpc_error = None
    try:
        context.last_rpc_result = context.runner.call(
            "email-notifier-service",
            method_name,
            extra_headers=extra_headers,
            **payload,
        )
    except Exception as exc:
        context.last_rpc_result = None
        context.last_rpc_error = exc


@then("the create-endpoint response is")
def step_create_endpoint_success_response(context):
    _assert_success_response(context)


@then("the list-endpoints response is")
def step_list_endpoints_success_response(context):
    _assert_success_response(context)


@then("the get-endpoint response is")
def step_get_endpoint_success_response(context):
    _assert_success_response(context)


@then("the delete-endpoint response is")
def step_delete_endpoint_success_response(context):
    _assert_success_response(context)


@then('the RPC call succeeds with status "{status}"')
@then('the ensure_auth_email_endpoint RPC call succeeds with status "{status}"')
def step_ensure_auth_email_endpoint_rpc_success(context, status):
    if context.last_rpc_error is not None:
        raise AssertionError(
            f"Expected RPC success, got error: {context.last_rpc_error}"
        )
    assert isinstance(context.last_rpc_result, dict), (
        "Expected RPC result to be a dict, " f"got {type(context.last_rpc_result)}"
    )
    actual_status = context.last_rpc_result.get("status")
    assert (
        actual_status == status
    ), f"Expected status={status}, got status={actual_status} payload={context.last_rpc_result}"


@then("the RPC response is")
@then("the ensure_auth_email_endpoint RPC response is")
def step_ensure_auth_email_endpoint_rpc_response(context):
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


@then("the RPC request is rejected due to validation error")
@then("the ensure_auth_email_endpoint request is rejected due to validation error")
def step_ensure_auth_email_endpoint_validation_error(context):
    expected = json.loads(context.text.strip()) if context.text else {}
    error = context.last_rpc_error
    assert error is not None, "Expected RPC validation error, but call succeeded."
    actual = {"code": error.code, "message": error.message}
    assert (
        actual == expected
    ), f"RPC error mismatch.\nExpected: {expected}\nActual:   {actual}"


@then("the RPC call fails with a {error_code}")
def step_rpc_call_fails_with_error_code(context, error_code):
    expected = json.loads(context.text.strip()) if context.text else {}
    error = context.last_rpc_error
    assert error is not None, "Expected RPC error, but call succeeded."
    actual = {
        "code": getattr(error, "code", None),
        "message": getattr(error, "message", None),
    }
    assert (
        actual.get("code") == error_code
    ), f"RPC error code mismatch.\nExpected: {error_code}\nActual:   {actual.get('code')}"
    if expected:
        assert (
            actual == expected
        ), f"RPC error mismatch.\nExpected: {expected}\nActual:   {actual}"


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
    _ = getattr(context, "last_published_event_payload", None)
    messages = mailhog.list_messages()
    assert not messages, f"Expected no email in MailHog, got {messages}"


@when("the email-notifier service fails to start with the following configuration")
def step_email_notifier_fails_to_start_with_config(context):
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
    context.email_notifier_config_path = config_path
    time.sleep(5)
    exit_code = proc.poll()
    stderr = (
        proc.stderr.read().decode(errors="replace") if proc.stderr else ""
    ) or "(empty)"
    if exit_code is None:
        proc.terminate()
        proc.wait(timeout=5)
        raise AssertionError(
            "Expected email-notifier startup to fail, but process is still running."
        )
    context.email_notifier_startup_stderr = stderr
    context.email_notifier_process = None


@then("the email-notifier service startup error mentions endpoints")
def step_email_notifier_startup_error_mentions_endpoints(context):
    stderr = getattr(context, "email_notifier_startup_stderr", "") or ""
    lowered = stderr.lower()
    assert "endpoints" in lowered, (
        "Expected startup error to mention endpoints.\n" f"stderr:\n{stderr}"
    )


@then("the service registry eventually receives a heartbeat with degraded flag true")
def step_registry_eventually_reports_degraded(context):
    amqp_url = _registry_amqp_url(context)
    deadline = time.time() + 20
    last_services = {}
    while time.time() < deadline:
        services = _fetch_registry_services(amqp_url)
        last_services = services
        email_service = services.get("email-notifier-service", {})
        if any(
            isinstance(instance_data, dict)
            and instance_data.get("status") == "degraded"
            for instance_data in email_service.values()
        ):
            return
        time.sleep(1)
    raise AssertionError(
        "Expected email-notifier-service to become degraded in service registry. "
        f"Last registry payload: {last_services}"
    )


@then("the create-endpoint call is rejected with HTTP {status_code:d}")
def step_create_endpoint_rejected_response(context, status_code):
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


@then("the get-endpoint call is rejected with HTTP {status_code:d}")
def step_get_endpoint_rejected_response(context, status_code):
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
