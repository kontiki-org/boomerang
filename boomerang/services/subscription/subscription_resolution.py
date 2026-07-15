def build_facts_from_alert(alert: dict) -> tuple[str, str, dict[str, list[str]]]:
    category = str(alert.get("category", "")).strip().lower()
    event_type = str(alert.get("event_type", "")).strip().lower()
    areas = alert.get("areas", [])
    first_area = areas[0] if isinstance(areas, list) and areas else {}
    area_type = str(first_area.get("type", "")).strip().lower()
    area_value = str(first_area.get("value", "")).strip()
    severity = str(alert.get("severity", "")).strip().lower()
    attributes = alert.get("attributes", {})
    attributes = attributes if isinstance(attributes, dict) else {}
    facts: dict[str, list[str]] = {
        "category": [category] if category else [],
        "event_type": [event_type] if event_type else [],
        "severity": [severity] if severity else [],
        "area_type": [area_type] if area_type else [],
        "area_value": [area_value] if area_value else [],
    }
    for area in areas if isinstance(areas, list) else []:
        if not isinstance(area, dict):
            continue
        item_type = str(area.get("type", "")).strip().lower()
        item_value = str(area.get("value", "")).strip()
        if not item_type or not item_value:
            continue
        facts.setdefault(f"area.{item_type}", []).append(item_value)
    for key, value in attributes.items():
        if not isinstance(key, str):
            continue
        normalized_key = key.strip().lower()
        if not normalized_key:
            continue
        facts.setdefault(normalized_key, []).append(str(value))
    return category, event_type, facts


def criteria_matches(criteria: dict, facts: dict[str, list[str]]) -> bool:
    all_of = criteria.get("all_of", [])
    if not isinstance(all_of, list):
        return False
    for item in all_of:
        if not isinstance(item, dict):
            return False
        key = str(item.get("key", "")).strip().lower()
        operator = str(item.get("operator", "")).strip().lower()
        expected = item.get("value")
        if key == "*" and str(expected).strip() == "*":
            continue
        if not key or operator not in {"eq", "gte", "lte", "contains"}:
            return False
        candidates = facts.get(key) or []
        if not candidates:
            return False
        if not any(
            _matches_operator(actual, expected, operator) for actual in candidates
        ):
            return False
    return True


def rule_matches_alert(rule_category: str, rule_event_type: str, category: str, event_type: str) -> bool:
    if rule_category != category:
        return False
    return rule_event_type == "*" or rule_event_type == event_type


def merge_recipients(*recipient_lists: list[dict]) -> list[dict]:
    seen: set[tuple[str, str, str]] = set()
    targets: list[dict] = []
    for recipients in recipient_lists:
        for item in recipients:
            key = (
                item["recipient_id"],
                item["channel"],
                item["endpoint_key"],
            )
            if key in seen:
                continue
            seen.add(key)
            targets.append(item)
    return sort_recipients(targets)


def sort_recipients(targets: list[dict]) -> list[dict]:
    return sorted(
        targets,
        key=lambda item: (
            item["recipient_id"],
            item["channel"],
            item["endpoint_key"],
        ),
    )


def _matches_operator(actual: str, expected: object, operator: str) -> bool:
    if operator == "contains":
        return str(expected).lower() in actual.lower()
    if operator == "eq":
        return actual.lower() == str(expected).lower()
    try:
        actual_num = float(actual)
        expected_num = float(expected)  # type: ignore[arg-type]
    except (ValueError, TypeError):
        return False
    if operator == "gte":
        return actual_num >= expected_num
    if operator == "lte":
        return actual_num <= expected_num
    return False
