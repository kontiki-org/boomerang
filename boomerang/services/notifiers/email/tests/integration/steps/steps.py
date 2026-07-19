import asyncio
import json
import time

import yaml
from behave import given, then, when
from boomerang_contracts.notification.message import NotificationRequest
from kontiki.messaging import Messenger, RpcClientError
from kontiki.registry.client.proxy import ServiceRegistryProxy
from pydantic import BaseModel

from boomerang.services.notifiers.email.tests.integration import mailhog
from boomerang.services.notifiers.email.tests.integration.utils import (
    http_request,
    start_email_notifier_subprocess,
)


def _last_response(context):
    return context.last_http_status, context.last_http_body


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
    config = context.email_notifier_config or {}
    return (
        config.get("kontiki", {}).get("amqp", {}).get("url")
        or "amqp://guest:guest@localhost/"
    )


def _fetch_registry_services(amqp_url):
    async def _fetch():
        async with Messenger(amqp_url=amqp_url, standalone=True) as messenger:
            proxy = ServiceRegistryProxy(messenger)
            return await proxy.get_services()

    return asyncio.run(_fetch())


def _assert_event_published(context, event_type):
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
    actual_payload = _as_jsonable(match.get("payload", {}))
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
    if context.last_access_token is not None:
        headers = headers or {}
        headers.setdefault("Authorization", f"Bearer {context.last_access_token}")
    status, resp_body = http_request(method, url, payload=body, headers=headers)
    context.last_http_status = status
    context.last_http_body = resp_body


@when(
    "I call the RPC {method_name} on the email-notifier service with the following arguments"
)
def step_call_rpc_on_email_notifier_service(context, method_name):
    payload_text = _resolve_placeholders(context.text.strip(), context)
    payload = json.loads(payload_text) if payload_text else {}
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
    _ = context.last_published_event_payload
    messages = mailhog.list_messages()
    assert not messages, f"Expected no email in MailHog, got {messages}"


@when("the email-notifier service fails to start with the following configuration")
def step_email_notifier_fails_to_start_with_config(context):
    config_text = context.text.strip()
    config = yaml.safe_load(config_text) or {}
    context.email_notifier_config = config

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
    stderr = context.email_notifier_startup_stderr or ""
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
