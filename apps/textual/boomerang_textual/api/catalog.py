from __future__ import annotations

from dataclasses import dataclass, field

from boomerang.core.contracts.alert_catalog import (
    AlertCriterionDescriptor,
    AlertSubscriptionCatalog,
)


@dataclass
class CatalogIndex:
    categories: list[tuple[str, str]] = field(default_factory=list)
    event_types_by_category: dict[str, list[tuple[str, str]]] = field(
        default_factory=dict
    )
    criteria_by_rule: dict[tuple[str, str], list[AlertCriterionDescriptor]] = field(
        default_factory=dict
    )


def catalog_from_rpc(raw) -> AlertSubscriptionCatalog:
    if isinstance(raw, AlertSubscriptionCatalog):
        return raw
    return AlertSubscriptionCatalog.model_validate(raw)


def build_catalog_index(catalog: AlertSubscriptionCatalog) -> CatalogIndex:
    categories: dict[str, str] = {}
    event_types: dict[str, dict[str, str]] = {}
    criteria: dict[tuple[str, str], dict[str, AlertCriterionDescriptor]] = {}

    for source in catalog.sources:
        for category in source.categories:
            categories[category.category] = category.label
            event_bucket = event_types.setdefault(category.category, {})
            criteria_bucket = criteria
            for event_type in category.event_types:
                event_bucket[event_type.event_type] = event_type.label
                rule_key = (category.category, event_type.event_type)
                descriptor_bucket = criteria_bucket.setdefault(rule_key, {})
                for descriptor in event_type.criteria:
                    descriptor_bucket[descriptor.key] = descriptor

    index = CatalogIndex()
    index.categories = [
        (label, category)
        for category, label in sorted(categories.items(), key=lambda item: item[1])
    ]
    for category, event_map in event_types.items():
        index.event_types_by_category[category] = [
            (label, event_type)
            for event_type, label in sorted(event_map.items(), key=lambda item: item[1])
        ]
    for rule_key, descriptor_map in criteria.items():
        index.criteria_by_rule[rule_key] = list(descriptor_map.values())
    return index
