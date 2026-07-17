import json
import sys
import time
from pathlib import Path

import yaml
from behave import given, then, when

_INTEGRATION_DIR = Path(__file__).resolve().parents[1]
if str(_INTEGRATION_DIR) not in sys.path:
    sys.path.insert(0, str(_INTEGRATION_DIR))

from utils import start_connector_subprocess

CATCHER = "alert-normalized-event-catcher"
SERVICE_NAME = "alert-connector-demo-service"


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


@given("the alert connector is running with the following configuration")
def step_connector_running_with_config(context):
    config = yaml.safe_load(context.text.strip()) or {}
    proc, config_path = start_connector_subprocess(config)
    context.connector_process = proc
    context.connector_config_path = config_path
    time.sleep(4)
    if proc.poll() is not None:
        stderr = (
            proc.stderr.read().decode(errors="replace") if proc.stderr else ""
        ) or "(empty)"
        raise RuntimeError(
            "Alert connector subprocess exited before step. stderr:\n%s" % stderr
        )


@when(
    "I call the RPC {method_name} on the alert connector with the following arguments"
)
def step_call_rpc_on_connector(context, method_name):
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


@then("the alert connector RPC call succeeds")
def step_connector_rpc_success(context):
    if context.last_rpc_error is not None:
        raise AssertionError(
            "Expected RPC success, got error: %s" % context.last_rpc_error
        )


@then("the alert connector RPC response is")
def step_connector_rpc_response(context):
    expected = json.loads(context.text.strip()) if context.text else {}
    actual = context.last_rpc_result
    if hasattr(actual, "model_dump"):
        actual = actual.model_dump(mode="json")
    assert actual == expected, "Expected %s, got %s" % (expected, actual)


@then('an "{event_type}" event is published with payload')
def step_an_event_published_with_payload(context, event_type):
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
    assert False, "No matching %s event.\nExpected: %s\nRecent events: %s" % (
        event_type,
        expected_payload,
        last_events,
    )
