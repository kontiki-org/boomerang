import json
import time

import yaml
from behave import given, then

from boomerang.services.alert_services.earthquake.tests.integration.utils import (
    start_earthquake_feed_subprocess,
)

CATCHER = "alert-normalized-event-catcher"
FEED_MOCK = "usgs-feed-mock"


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


@given("the HTTP feed mock returns GeoJSON with one new feature")
@given("the HTTP feed mock returns GeoJSON with one feature below min_magnitude")
def step_feed_mock_returns_geojson(context):
    doc = json.loads(context.text.strip()) if context.text else {}
    context.manager.add_http_response(FEED_MOCK, doc)


@given("the earthquake-feed-service is running with the following configuration")
def step_earthquake_feed_running_with_config(context):
    config_text = context.text.strip()
    config = yaml.safe_load(config_text) or {}
    proc, config_path = start_earthquake_feed_subprocess(config)
    context.earthquake_feed_process = proc
    context.earthquake_feed_config_path = config_path
    time.sleep(6)
    if proc.poll() is not None:
        stderr = (
            proc.stderr.read().decode(errors="replace") if proc.stderr else ""
        ) or "(empty)"
        raise RuntimeError(
            "Earthquake feed subprocess exited before step. stderr:\n%s" % stderr
        )


@when("the earthquake feed completes a poll cycle")
def step_earthquake_poll_cycle(context):
    _ = context
    time.sleep(2)


@then('an "{event_type}" event is published with payload')
def step_an_event_published_with_payload(context, event_type):
    expected_payload = json.loads(context.text.strip()) if context.text else {}
    deadline = time.time() + 15
    last_events: list = []
    while time.time() < deadline:
        last_events = (
            context.manager.get_events(CATCHER, wait_for_events=1, timeout=2) or []
        )
        for event in last_events:
            if event.get("event_type") != event_type:
                continue
            actual_payload = event.get("payload", {})
            if hasattr(actual_payload, "model_dump"):
                actual_payload = actual_payload.model_dump()
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


@then('no "{event_type}" event is published')
def step_no_event_published(context, event_type):
    time.sleep(2)
    events = context.manager.get_events(CATCHER, wait_for_events=1, timeout=2) or []
    matches = [e for e in events if e.get("event_type") == event_type]
    assert not matches, f"Unexpected {event_type} events: {matches}"
    context.manager.clean_events(CATCHER)
