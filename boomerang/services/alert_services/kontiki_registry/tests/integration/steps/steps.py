import json
import time

import yaml
from behave import given, then, when

from boomerang.services.alert_services.kontiki_registry.tests.integration.utils import (
    start_kontiki_registry_alert_subprocess,
)

CATCHER = "alert-normalized-event-catcher"
SERVICE_NAME = "kontiki-registry-alert-service"
PUBLISHER_NAME = "notification-publisher"


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

    return actual


@given("the kontiki-registry-alert-service is running with the following configuration")
def step_service_running_with_configuration(context):
    config_text = context.text.strip()
    config = yaml.safe_load(config_text) or {}
    proc, config_path = start_kontiki_registry_alert_subprocess(config)
    context.kontiki_registry_alert_process = proc
    context.kontiki_registry_alert_config_path = config_path
    time.sleep(5)
    if proc.poll() is not None:
        stderr = (
            proc.stderr.read().decode(errors="replace") if proc.stderr else ""
        ) or "(empty)"
        raise RuntimeError(
            "Kontiki registry alert subprocess exited before step. stderr:\n%s" % stderr
        )


@when('a "{event_type}" event is published with payload')
def step_publish_registry_event_with_payload(context, event_type):
    payload = json.loads(context.text.strip()) if context.text else {}
    context.runner.call(
        PUBLISHER_NAME,
        "publish_event",
        event_type=event_type,
        payload=payload,
    )
    time.sleep(1)


@then('an "{event_type}" event is published with payload')
def step_assert_event_with_payload(context, event_type):
    expected_payload = json.loads(context.text.strip()) if context.text else {}
    deadline = time.time() + 15
    last_events = []
    while time.time() < deadline:
        last_events = (
            context.manager.get_events(CATCHER, wait_for_events=1, timeout=2) or []
        )
        for event in last_events:
            if event.get("event_type") != event_type:
                continue
            actual_payload = event.get("payload", {})
            if hasattr(actual_payload, "model_dump"):
                actual_payload = actual_payload.model_dump(mode="json")
            normalized = _normalize_actual_for_placeholders(
                expected_payload, actual_payload
            )
            if normalized == expected_payload:
                context.manager.clean_events(CATCHER)
                return
        time.sleep(0.25)

    assert False, (
        f"No matching {event_type} event.\n"
        f"Expected: {expected_payload}\n"
        f"Recent events: {last_events}"
    )


@when(
    "I call the RPC {method_name} on the kontiki-registry-alert service with the following arguments"
)
def step_call_rpc(context, method_name):
    payload = json.loads(context.text.strip()) if context.text else {}
    context.last_rpc_error = None
    try:
        context.last_rpc_result = context.runner.call(
            SERVICE_NAME,
            method_name,
            **payload,
        )
    except Exception as exc:
        context.last_rpc_result = None
        context.last_rpc_error = exc


@then("the kontiki-registry-alert RPC call succeeds")
def step_rpc_succeeds(context):
    if context.last_rpc_error is not None:
        raise AssertionError(
            f"Expected RPC success, got error: {context.last_rpc_error}"
        )


@then("the kontiki-registry-alert RPC response is")
def step_rpc_response_is(context):
    expected = json.loads(context.text.strip()) if context.text else {}
    actual = context.last_rpc_result
    if hasattr(actual, "model_dump"):
        actual = actual.model_dump(mode="json")
    assert actual == expected, f"Expected {expected}, got {actual}"
