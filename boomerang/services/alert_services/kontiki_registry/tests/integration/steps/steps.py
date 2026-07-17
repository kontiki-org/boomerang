import json
import time

import yaml
from behave import given, then, when
from pydantic import BaseModel

from boomerang.services.alert_services.kontiki_registry.fleet_state import (
    FLEET_POLL_INTERVAL_SECONDS,
)
from boomerang.services.alert_services.kontiki_registry.tests.integration.utils import (
    start_kontiki_registry_alert_subprocess,
)

CATCHER = "alert-normalized-event-catcher"
SERVICE_NAME = "kontiki-registry-alert-service"
PUBLISHER_NAME = "notification-publisher"
REGISTRY_MOCK = "ServiceRegistry"


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


def _payload_as_dict(payload):
    if isinstance(payload, dict):
        return payload
    if isinstance(payload, BaseModel):
        return payload.model_dump(mode="json")
    return payload


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


@when("a fleet poll observes the Service Registry returning the following services")
def step_fleet_poll_observes_registry_services(context):
    services = json.loads(context.text.strip()) if context.text else {}
    context.manager.get_service(REGISTRY_MOCK).set_services(services)
    context.manager.clean_events(CATCHER)
    # Wait through one real @task cycle (immediate=False, interval hardcoded).
    time.sleep(FLEET_POLL_INTERVAL_SECONDS + 5)


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
            actual_payload = _payload_as_dict(event.get("payload", {}))
            normalized = _normalize_actual_for_placeholders(
                expected_payload, actual_payload
            )
            if normalized == expected_payload:
                return
        time.sleep(0.25)

    assert False, (
        "No matching %s event.\nExpected: %s\nRecent events: %s"
        % (event_type, expected_payload, last_events)
    )


@then('no "{event_type}" event is published')
def step_no_event_published(context, event_type):
    time.sleep(1)
    events = context.manager.get_events(CATCHER, wait_for_events=1, timeout=1) or []
    matching = [event for event in events if event.get("event_type") == event_type]
    assert not matching, "Unexpected %s events: %s" % (event_type, matching)


@then('no "{event_type}" event is published with event_type "{inner_event_type}"')
def step_no_alert_with_inner_event_type(context, event_type, inner_event_type):
    time.sleep(0.5)
    events = context.manager.get_events(CATCHER, wait_for_events=1, timeout=1) or []
    for event in events:
        if event.get("event_type") != event_type:
            continue
        payload = _payload_as_dict(event.get("payload", {}))
        if payload.get("event_type") == inner_event_type:
            assert False, "Unexpected alert with event_type=%s: %s" % (
                inner_event_type,
                payload,
            )


@then('no "{event_type}" event is published for service_name "{service_name}"')
def step_no_alert_for_service_name(context, event_type, service_name):
    time.sleep(0.5)
    events = context.manager.get_events(CATCHER, wait_for_events=1, timeout=1) or []
    for event in events:
        if event.get("event_type") != event_type:
            continue
        payload = _payload_as_dict(event.get("payload", {}))
        attributes = payload.get("attributes") or {}
        if attributes.get("service_name") == service_name:
            assert False, "Unexpected alert for service_name=%s: %s" % (
                service_name,
                payload,
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
            "Expected RPC success, got error: %s" % context.last_rpc_error
        )


@then("the kontiki-registry-alert RPC response is")
def step_rpc_response_is(context):
    expected = json.loads(context.text.strip()) if context.text else {}
    actual = _payload_as_dict(context.last_rpc_result)
    assert actual == expected, "Expected %s, got %s" % (expected, actual)


@then("the kontiki-registry-alert RPC response includes the event types")
def step_rpc_response_includes_event_types(context):
    expected_event_types = json.loads(context.text.strip()) if context.text else []
    actual = _payload_as_dict(context.last_rpc_result)
    categories = actual.get("categories") or []
    found = []
    for category in categories:
        found.extend(category.get("event_types") or [])
    by_type = {item.get("event_type"): item for item in found}
    for expected in expected_event_types:
        event_type = expected.get("event_type")
        assert event_type in by_type, "Missing event_type %s in %s" % (
            event_type,
            list(by_type),
        )
        assert by_type[event_type] == expected, (
            "Event type mismatch for %s: %s vs %s"
            % (event_type, by_type[event_type], expected)
        )
