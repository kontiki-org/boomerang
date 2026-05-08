import json
import time

import yaml
from behave import given, then, when

from boomerang.services.alert_engine.tests.integration.utils import (
    start_alert_engine_subprocess,
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

    return actual


@given("the alert-engine service is running with the following configuration")
def step_alert_engine_running_with_config(context):
    config_text = context.text.strip()
    config = yaml.safe_load(config_text) or {}
    proc, config_path = start_alert_engine_subprocess(config)
    context.alert_engine_process = proc
    context.alert_engine_config_path = config_path
    time.sleep(5)
    if proc.poll() is not None:
        stderr = (
            proc.stderr.read().decode(errors="replace") if proc.stderr else ""
        ) or "(empty)"
        raise RuntimeError(
            "AlertEngine subprocess exited before step. stderr:\n%s" % stderr
        )


DISPATCH_EVENT_CATCHER = "notification-dispatch-event-catcher"


@when('a "{event_type}" event is published with payload')
def step_publish_event_with_payload(context, event_type):
    payload = json.loads(context.text.strip()) if context.text else {}
    context.last_published_event_payload = payload
    context._matched_dispatch_sigs = []
    context.runner.call(
        "notification-publisher",
        "publish_event",
        event_type=event_type,
        payload=payload,
    )
    time.sleep(1)


@then("the alert-engine calls subscription RPC get_recipients_for_alert with")
def step_alert_engine_calls_subscription_rpc(context):
    expected_args = json.loads(context.text.strip()) if context.text else {}
    calls = context.manager.get_remote_calls("subscription-service") or []
    assert calls, "Expected one call to subscription-service.get_recipients_for_alert."
    first_call = calls[0]
    args = ()
    if isinstance(first_call, (list, tuple)):
        args = first_call[0] if first_call else ()
    assert isinstance(args, (list, tuple)), f"Unexpected call format: {first_call}"
    assert len(args) >= 1, f"Unexpected RPC args payload: {args}"
    actual_args = args[0]
    normalized = _normalize_actual_for_placeholders(expected_args, actual_args)
    assert isinstance(normalized, dict), f"Unexpected alert args payload: {actual_args}"
    assert normalized == expected_args, (
        "RPC call arguments mismatch.\n"
        f"Expected: {expected_args}\n"
        f"Actual:   {normalized}"
    )


@when("the alert-engine receives recipients from subscription RPC")
def step_alert_engine_receives_recipients(context):
    expected = json.loads(context.text.strip()) if context.text else []
    actual = getattr(context, "expected_subscription_recipients", [])
    normalized = _normalize_actual_for_placeholders(expected, actual)
    assert normalized == expected, (
        "Recipients mismatch for subscription RPC response.\n"
        f"Expected: {expected}\n"
        f"Actual:   {normalized}"
    )


def _dispatch_match_signature(event_type, payload):
    if not isinstance(payload, dict):
        return (event_type, None, None)
    return (
        event_type,
        payload.get("recipient_id"),
        payload.get("endpoint_key"),
    )


def _assert_dispatch_event_published(context, event_type):
    expected_payload = json.loads(context.text.strip()) if context.text else {}
    matched = getattr(context, "_matched_dispatch_sigs", None) or []
    deadline = time.time() + 15
    last_events = []
    while time.time() < deadline:
        last_events = (
            context.manager.get_events(
                DISPATCH_EVENT_CATCHER, wait_for_events=1, timeout=2
            )
            or []
        )
        for event in last_events:
            if event.get("event_type") != event_type:
                continue
            actual_payload = event.get("payload", {})
            if hasattr(actual_payload, "model_dump"):
                actual_payload = actual_payload.model_dump()
            sig = _dispatch_match_signature(event_type, actual_payload)
            if sig in matched:
                continue
            normalized = _normalize_actual_for_placeholders(
                expected_payload, actual_payload
            )
            if normalized == expected_payload:
                matched = list(matched) + [sig]
                context._matched_dispatch_sigs = matched
                return
        time.sleep(0.25)
    assert False, (
        f"No matching {event_type} event.\n"
        f"Expected: {expected_payload}\n"
        f"Recent events: {last_events}"
    )


@then('an "{event_type}" event is published')
def step_an_event_is_published(context, event_type):
    _assert_dispatch_event_published(context, event_type)


@then('a "{event_type}" event is published')
def step_a_event_is_published(context, event_type):
    _assert_dispatch_event_published(context, event_type)


@then('no "{event_type}" event is published')
def step_no_event_is_published(context, event_type):
    events = context.manager.get_events(
        DISPATCH_EVENT_CATCHER, wait_for_events=1, timeout=2
    )
    matches = [event for event in events if event.get("event_type") == event_type]
    assert not matches, f"Unexpected event {event_type} found: {matches}"
