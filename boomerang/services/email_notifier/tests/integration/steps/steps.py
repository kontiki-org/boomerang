import json
import sqlite3
import time
from pathlib import Path

import yaml
from behave import given, then, when

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

