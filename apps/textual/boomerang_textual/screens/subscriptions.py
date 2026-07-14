from __future__ import annotations

from boomerang.core.contracts.alert_catalog import AlertCriterionDescriptor
from boomerang.core.contracts.subscription import (
    CreateSubscriptionRequest,
    CriteriaExpression,
    Criterion,
    EndpointRef,
    RuleDefinition,
    SubscriptionDefinition,
    UpdateSubscriptionRequest,
)
from boomerang_textual.api import build_catalog_index, catalog_from_rpc, rpc_error_message
from boomerang_textual.api.catalog import CatalogIndex
from textual.containers import Horizontal, Vertical
from textual.message import Message
from textual.widgets import Button, DataTable, Input, Label, Select, Static

OPERATOR_LABELS: dict[str, str] = {
    "eq": "equals",
    "gte": "greater or equal",
    "lte": "less or equal",
    "contains": "contains",
}


class SubscriptionsScreen(Static):
    EMPTY_CRITERION_KEY = "__none__"
    EMPTY_ENDPOINT_VALUE = "__none__"

    class StatusMessage(Message):
        def __init__(self, text: str, level: str = "info") -> None:
            super().__init__()
            self.text = text
            self.level = level

    def __init__(self) -> None:
        super().__init__()
        self._subscriptions: list[dict] = []
        self._catalog_index: CatalogIndex | None = None
        self._available_endpoints: list[dict[str, str]] = []
        self._selected_endpoints: list[dict[str, str]] = []
        self._editing_subscription_id: str | None = None

    def compose(self):
        with Horizontal(id="subscriptions-layout"):
            with Vertical(id="subscriptions-form-pane"):
                yield Static("Create or update subscription", classes="section-title")
                with Horizontal(id="subscriptions-form-line-1"):
                    with Vertical(classes="field-group"):
                        yield Label("Alert category", classes="field-label")
                        yield Select(
                            options=[("Loading catalog…", "")],
                            value="",
                            id="subscription-category",
                        )
                    with Vertical(classes="field-group"):
                        yield Label("Event type", classes="field-label")
                        yield Select(
                            options=[("—", "")],
                            value="",
                            id="subscription-event-type",
                        )
                with Horizontal(id="subscriptions-form-line-2"):
                    with Vertical(classes="field-group"):
                        yield Label("Criterion key (optional)", classes="field-label")
                        yield Select(
                            options=[("No criterion", self.EMPTY_CRITERION_KEY)],
                            value=self.EMPTY_CRITERION_KEY,
                            id="subscription-criterion-key",
                        )
                    with Vertical(classes="field-group"):
                        yield Label("Operator (optional)", classes="field-label")
                        yield Select(
                            options=[("equals", "eq")],
                            value="eq",
                            id="subscription-criterion-operator",
                        )
                    with Vertical(classes="field-group"):
                        yield Label("Criterion value (optional)", classes="field-label")
                        yield Input(
                            placeholder="example: 4.5 / FR-69",
                            id="subscription-criterion-value",
                        )
                with Horizontal(id="subscriptions-form-line-status"):
                    with Vertical(classes="field-group"):
                        yield Label("Status", classes="field-label")
                        yield Select(
                            options=[
                                ("active", "active"),
                                ("paused", "paused"),
                            ],
                            value="active",
                            id="subscription-status",
                        )
                with Horizontal(id="subscriptions-form-line-3"):
                    with Vertical(classes="field-group"):
                        yield Label("Endpoint to add", classes="field-label")
                        yield Select(
                            options=[
                                ("No endpoint available", self.EMPTY_ENDPOINT_VALUE)
                            ],
                            value=self.EMPTY_ENDPOINT_VALUE,
                            id="subscription-endpoint-select",
                        )
                    with Vertical(classes="field-group"):
                        yield Label("Selection actions", classes="field-label")
                        with Horizontal(id="subscriptions-endpoint-actions"):
                            yield Button(
                                "Add endpoint",
                                id="add-subscription-endpoint-btn",
                                variant="primary",
                            )
                            yield Button(
                                "Remove selected endpoint",
                                id="remove-subscription-endpoint-btn",
                                variant="warning",
                            )
                with Vertical(id="subscriptions-selected-endpoints-pane"):
                    yield Label("Selected endpoints", classes="field-label")
                    selected_table = DataTable(
                        id="subscription-selected-endpoints",
                        cursor_type="row",
                    )
                    selected_table.add_columns("Type", "Endpoint key", "Destination")
                    yield selected_table
                with Horizontal(id="subscriptions-form-actions"):
                    yield Button(
                        "New subscription",
                        id="new-subscription-btn",
                    )
                    yield Button(
                        "Save subscription",
                        id="save-subscription-btn",
                        variant="primary",
                    )
                    yield Button(
                        "Delete selected",
                        id="delete-subscription-btn",
                        variant="error",
                    )
            with Vertical(id="subscriptions-list-pane"):
                yield Static("Registered subscriptions", classes="section-title")
                table = DataTable(id="subscriptions-list", cursor_type="row")
                table.add_columns(
                    "Category",
                    "Event type",
                    "Criteria",
                    "Endpoints",
                    "Status",
                )
                yield table

    async def on_mount(self) -> None:
        await self.reload_data()

    async def reload_data(self) -> None:
        await self._reload_catalog()
        await self._reload_subscriptions()
        self._sync_endpoint_select_options()
        self._refresh_selected_endpoints_list()

    async def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "save-subscription-btn":
            await self._handle_save_subscription()
            return
        if event.button.id == "delete-subscription-btn":
            await self._handle_delete_selected()
            return
        if event.button.id == "new-subscription-btn":
            self._clear_form()
            self.post_message(self.StatusMessage("Ready to create a subscription.", "info"))
            return
        if event.button.id == "add-subscription-endpoint-btn":
            self._handle_add_selected_endpoint()
            return
        if event.button.id == "remove-subscription-endpoint-btn":
            self._handle_remove_selected_endpoint()

    def on_data_table_row_selected(self, event: DataTable.RowSelected) -> None:
        if event.data_table.id != "subscriptions-list":
            return
        if event.cursor_row is None or event.cursor_row < 0:
            return
        if event.cursor_row >= len(self._subscriptions):
            return
        self._load_subscription_into_form(self._subscriptions[event.cursor_row])

    def on_select_changed(self, event: Select.Changed) -> None:
        if event.select.id == "subscription-category":
            selected_category = event.value if isinstance(event.value, str) else ""
            self._sync_event_type_options(selected_category=selected_category)
            self._sync_criterion_key_options(selected_category=selected_category)
        elif event.select.id == "subscription-event-type":
            selected_event_type = event.value if isinstance(event.value, str) else ""
            self._sync_criterion_key_options(selected_event_type=selected_event_type)
        elif event.select.id == "subscription-criterion-key":
            self._sync_criterion_operator_options()

    def _auth_headers(self) -> dict[str, str] | None:
        token = self.app.session.access_token  # type: ignore[attr-defined]
        if not token:
            return None
        return {"Authorization": f"Bearer {token}"}

    def _subscription_rpc(self):
        return self.app.subscription_rpc  # type: ignore[attr-defined]

    async def _reload_catalog(self) -> None:
        rpc = self._subscription_rpc()
        if rpc is None:
            return
        try:
            raw = await rpc.get_alert_subscription_catalog()
            catalog = catalog_from_rpc(raw)
            self._catalog_index = build_catalog_index(catalog)
        except Exception as exc:
            self._catalog_index = CatalogIndex()
            self.post_message(
                self.StatusMessage(
                    f"Could not load alert catalog: {rpc_error_message(exc)}",
                    "error",
                )
            )
        self._sync_category_options()

    async def _reload_subscriptions(self) -> None:
        headers = self._auth_headers()
        if headers is None:
            self._subscriptions = []
            self._refresh_list()
            return
        rpc = self._subscription_rpc()
        if rpc is None:
            return
        try:
            result = await rpc.get_subscriptions(extra_headers=headers)
        except Exception as exc:
            self.post_message(self.StatusMessage(rpc_error_message(exc), "error"))
            self._subscriptions = []
            self._refresh_list()
            return
        items = result.get("items", []) if isinstance(result, dict) else []
        self._subscriptions = items if isinstance(items, list) else []
        self._refresh_list()

    def _sync_category_options(self) -> None:
        category_select = self.query_one("#subscription-category", Select)
        index = self._catalog_index
        if index is None or not index.categories:
            category_select.set_options([("No alert source available", "")])
            category_select.value = ""
            self._sync_event_type_options(selected_category="")
            return
        category_select.set_options(index.categories)
        category_select.value = index.categories[0][1]
        self._sync_event_type_options(selected_category=category_select.value)
        self._sync_criterion_key_options(selected_category=category_select.value)

    def _sync_event_type_options(
        self,
        selected_category: str | None = None,
        preferred_event_type: str | None = None,
    ) -> None:
        category_select = self.query_one("#subscription-category", Select)
        event_select = self.query_one("#subscription-event-type", Select)
        category = selected_category or category_select.value or ""
        available = []
        if self._catalog_index is not None:
            available = self._catalog_index.event_types_by_category.get(str(category), [])
        if not available:
            event_select.set_options([("—", "")])
            event_select.value = ""
            return
        event_select.set_options(available)
        values = {value for _, value in available}
        if preferred_event_type in values:
            event_select.value = preferred_event_type
        else:
            event_select.value = available[0][1]

    def _descriptor_for_key(
        self, category: str, event_type: str, criterion_key: str
    ) -> AlertCriterionDescriptor | None:
        if self._catalog_index is None:
            return None
        for descriptor in self._catalog_index.criteria_by_rule.get(
            (category, event_type), []
        ):
            if descriptor.key == criterion_key:
                return descriptor
        return None

    def _sync_criterion_key_options(
        self,
        selected_category: str | None = None,
        selected_event_type: str | None = None,
        preferred_criterion_key: str | None = None,
    ) -> None:
        category_select = self.query_one("#subscription-category", Select)
        event_select = self.query_one("#subscription-event-type", Select)
        criterion_select = self.query_one("#subscription-criterion-key", Select)
        category = selected_category or category_select.value or ""
        event_type = selected_event_type or event_select.value or ""
        descriptors = []
        if self._catalog_index is not None:
            descriptors = self._catalog_index.criteria_by_rule.get(
                (str(category), str(event_type)), []
            )
        options = [("No criterion", self.EMPTY_CRITERION_KEY)] + [
            (descriptor.label, descriptor.key) for descriptor in descriptors
        ]
        criterion_select.set_options(options)
        keys = {descriptor.key for descriptor in descriptors}
        if preferred_criterion_key and preferred_criterion_key in keys:
            criterion_select.value = preferred_criterion_key
        else:
            criterion_select.value = self.EMPTY_CRITERION_KEY
        self._sync_criterion_operator_options()

    def _sync_criterion_operator_options(self) -> None:
        operator_select = self.query_one("#subscription-criterion-operator", Select)
        category = self.query_one("#subscription-category", Select).value or ""
        event_type = self.query_one("#subscription-event-type", Select).value or ""
        criterion_key = self.query_one("#subscription-criterion-key", Select).value or ""
        if criterion_key == self.EMPTY_CRITERION_KEY:
            operator_select.set_options([(OPERATOR_LABELS["eq"], "eq")])
            operator_select.value = "eq"
            return
        descriptor = self._descriptor_for_key(
            str(category), str(event_type), str(criterion_key)
        )
        if descriptor is None:
            operator_select.set_options([(OPERATOR_LABELS["eq"], "eq")])
            operator_select.value = "eq"
            return
        options = [
            (OPERATOR_LABELS.get(operator, operator), operator)
            for operator in descriptor.operators
        ]
        operator_select.set_options(options)
        operator_select.value = options[0][1]

    def _parse_criterion_value(self, raw: str, descriptor: AlertCriterionDescriptor | None):
        value = raw.strip()
        kind = descriptor.value_kind if descriptor is not None else "string"
        if kind == "number":
            return float(value) if "." in value else int(value)
        if kind == "boolean":
            lowered = value.lower()
            if lowered in {"true", "1", "yes"}:
                return True
            if lowered in {"false", "0", "no"}:
                return False
            raise ValueError("Expected true or false.")
        return value

    def _build_rule_from_form(self) -> RuleDefinition:
        category = str(self.query_one("#subscription-category", Select).value or "")
        event_type = str(self.query_one("#subscription-event-type", Select).value or "")
        criterion_key = self.query_one("#subscription-criterion-key", Select).value or ""
        criterion_operator = (
            self.query_one("#subscription-criterion-operator", Select).value or "eq"
        )
        criterion_value = (
            self.query_one("#subscription-criterion-value", Input).value or ""
        ).strip()

        if not category or not event_type:
            raise ValueError("Select an alert category and event type.")

        if criterion_key == self.EMPTY_CRITERION_KEY:
            criterion_key = ""
        if bool(criterion_key) != bool(criterion_value):
            raise ValueError("Criterion key and value must be provided together.")
        if not criterion_key:
            criteria = CriteriaExpression(
                all_of=[Criterion(key="*", operator="eq", value="*")]
            )
        else:
            descriptor = self._descriptor_for_key(category, event_type, criterion_key)
            parsed_value = self._parse_criterion_value(criterion_value, descriptor)
            criteria = CriteriaExpression(
                all_of=[
                    Criterion(
                        key=str(criterion_key),
                        operator=criterion_operator,
                        value=parsed_value,
                    )
                ]
            )
        return RuleDefinition(
            category=category,
            event_type=event_type,
            criteria=criteria,
        )

    def _endpoint_refs_from_selection(self) -> list[EndpointRef]:
        if not self._selected_endpoints:
            raise ValueError("Please add at least one endpoint from the Endpoints tab.")
        return [
            EndpointRef(kind=endpoint["kind"], endpoint_key=endpoint["endpoint_key"])
            for endpoint in self._selected_endpoints
        ]

    async def _handle_save_subscription(self) -> None:
        headers = self._auth_headers()
        if headers is None:
            self.post_message(self.StatusMessage("Not signed in.", "error"))
            return
        rpc = self._subscription_rpc()
        if rpc is None:
            return
        try:
            rule = self._build_rule_from_form()
            endpoints = self._endpoint_refs_from_selection()
        except ValueError as exc:
            self.post_message(self.StatusMessage(str(exc), "error"))
            return
        except Exception:
            self.post_message(self.StatusMessage("Invalid criterion value.", "error"))
            return

        status = str(self.query_one("#subscription-status", Select).value or "active")

        try:
            if self._editing_subscription_id:
                body = UpdateSubscriptionRequest(
                    rule=rule,
                    endpoints=endpoints,
                    status=status,  # type: ignore[arg-type]
                )
                await rpc.update_subscription(
                    subscription_id=self._editing_subscription_id,
                    body=body,
                    extra_headers=headers,
                )
                message = "Subscription updated."
            else:
                body = CreateSubscriptionRequest(
                    subscription=SubscriptionDefinition(rule=rule, endpoints=endpoints)
                )
                result = await rpc.create_subscription(body=body, extra_headers=headers)
                errors = result.get("errors", []) if isinstance(result, dict) else []
                if errors:
                    first = errors[0]
                    detail = first.get("message", "Create failed.") if isinstance(first, dict) else "Create failed."
                    self.post_message(self.StatusMessage(detail, "error"))
                    return
                skipped = result.get("skipped", []) if isinstance(result, dict) else []
                if skipped:
                    self.post_message(
                        self.StatusMessage(
                            "An identical subscription already exists.",
                            "info",
                        )
                    )
                    return
                message = "Subscription created."
        except Exception as exc:
            self.post_message(self.StatusMessage(rpc_error_message(exc), "error"))
            return

        self._clear_form()
        await self._reload_subscriptions()
        self.post_message(self.StatusMessage(message, "success"))

    async def _handle_delete_selected(self) -> None:
        subscriptions_list = self.query_one("#subscriptions-list", DataTable)
        if subscriptions_list.cursor_row is None or subscriptions_list.cursor_row < 0:
            self.post_message(self.StatusMessage("No subscription selected.", "error"))
            return
        if subscriptions_list.cursor_row >= len(self._subscriptions):
            self.post_message(self.StatusMessage("Invalid selection.", "error"))
            return

        subscription_id = self._subscriptions[subscriptions_list.cursor_row][
            "subscription_id"
        ]
        headers = self._auth_headers()
        if headers is None:
            self.post_message(self.StatusMessage("Not signed in.", "error"))
            return
        rpc = self._subscription_rpc()
        if rpc is None:
            return
        try:
            await rpc.delete_subscription(
                subscription_id=subscription_id,
                extra_headers=headers,
            )
        except Exception as exc:
            self.post_message(self.StatusMessage(rpc_error_message(exc), "error"))
            return

        self._clear_form()
        await self._reload_subscriptions()
        self.post_message(self.StatusMessage("Subscription deleted.", "success"))

    def _clear_form(self) -> None:
        self._editing_subscription_id = None
        self._selected_endpoints = []
        self.query_one("#subscription-criterion-value", Input).value = ""
        self.query_one("#subscription-status", Select).value = "active"
        if self._catalog_index and self._catalog_index.categories:
            self._sync_category_options()
        self._refresh_selected_endpoints_list()

    def _load_subscription_into_form(self, item: dict) -> None:
        subscription = item.get("subscription", {})
        rule = subscription.get("rule", {})
        category = rule.get("category", "")
        event_type = rule.get("event_type", "")
        self._editing_subscription_id = item.get("subscription_id")
        self.query_one("#subscription-category", Select).value = category
        self._sync_event_type_options(
            selected_category=category,
            preferred_event_type=event_type,
        )
        self.query_one("#subscription-event-type", Select).value = event_type

        criteria = rule.get("criteria", {}).get("all_of", [])
        preferred_key = self.EMPTY_CRITERION_KEY
        operator = "eq"
        value = ""
        if (
            len(criteria) == 1
            and criteria[0].get("key") == "*"
            and criteria[0].get("value") == "*"
        ):
            pass
        elif criteria:
            first = criteria[0]
            preferred_key = first.get("key", self.EMPTY_CRITERION_KEY)
            operator = first.get("operator", "eq")
            value = str(first.get("value", ""))

        self._sync_criterion_key_options(
            selected_category=category,
            selected_event_type=event_type,
            preferred_criterion_key=preferred_key,
        )
        self.query_one("#subscription-criterion-key", Select).value = preferred_key
        self._sync_criterion_operator_options()
        self.query_one("#subscription-criterion-operator", Select).value = operator
        self.query_one("#subscription-criterion-value", Input).value = value
        self.query_one("#subscription-status", Select).value = item.get("status", "active")

        self._selected_endpoints = []
        for endpoint in subscription.get("endpoints", []):
            kind = endpoint.get("kind", "")
            endpoint_key = endpoint.get("endpoint_key", "")
            display = ""
            for available in self._available_endpoints:
                if (
                    available.get("kind") == kind
                    and available.get("endpoint_key") == endpoint_key
                ):
                    display = available.get("display", "")
                    break
            self._selected_endpoints.append(
                {
                    "kind": kind,
                    "endpoint_key": endpoint_key,
                    "display": display,
                }
            )
        self._refresh_selected_endpoints_list()

    def set_available_endpoints(self, endpoints: list[dict[str, str]]) -> None:
        self._available_endpoints = list(endpoints)
        self._sync_endpoint_select_options()

    def _sync_endpoint_select_options(self) -> None:
        endpoint_select = self.query_one("#subscription-endpoint-select", Select)
        options = []
        for endpoint in self._available_endpoints:
            kind = endpoint.get("kind", "").strip().lower()
            endpoint_key = endpoint.get("endpoint_key", "").strip()
            display = endpoint.get("display", "").strip()
            if not kind or not endpoint_key:
                continue
            label = f"{kind} | {endpoint_key} | {display or '-'}"
            value = f"{kind}:{endpoint_key}"
            options.append((label, value))
        if not options:
            endpoint_select.set_options(
                [("No endpoint available", self.EMPTY_ENDPOINT_VALUE)]
            )
            endpoint_select.value = self.EMPTY_ENDPOINT_VALUE
            return
        endpoint_select.set_options(options)
        if endpoint_select.value not in {value for _, value in options}:
            endpoint_select.value = options[0][1]

    def _handle_add_selected_endpoint(self) -> None:
        endpoint_select = self.query_one("#subscription-endpoint-select", Select)
        selected_value = endpoint_select.value or self.EMPTY_ENDPOINT_VALUE
        if selected_value == self.EMPTY_ENDPOINT_VALUE:
            self.post_message(self.StatusMessage("No endpoint to add.", "error"))
            return
        kind, _, endpoint_key = str(selected_value).partition(":")
        endpoint = next(
            (
                item
                for item in self._available_endpoints
                if item.get("kind") == kind and item.get("endpoint_key") == endpoint_key
            ),
            None,
        )
        if endpoint is None:
            self.post_message(
                self.StatusMessage(
                    "Selected endpoint is no longer available.",
                    "error",
                )
            )
            self._sync_endpoint_select_options()
            return
        already_selected = any(
            item.get("kind") == kind and item.get("endpoint_key") == endpoint_key
            for item in self._selected_endpoints
        )
        if already_selected:
            self.post_message(self.StatusMessage("Endpoint already selected.", "info"))
            return
        self._selected_endpoints.append(
            {
                    "kind": endpoint["kind"],
                    "endpoint_key": endpoint["endpoint_key"],
                    "display": endpoint.get("display", ""),
            }
        )
        self._refresh_selected_endpoints_list()
        self.post_message(self.StatusMessage("Endpoint added to subscription.", "success"))

    def _handle_remove_selected_endpoint(self) -> None:
        selected_list = self.query_one("#subscription-selected-endpoints", DataTable)
        if selected_list.cursor_row is None or selected_list.cursor_row < 0:
            self.post_message(self.StatusMessage("No selected endpoint row.", "error"))
            return
        if selected_list.cursor_row >= len(self._selected_endpoints):
            self.post_message(self.StatusMessage("Invalid endpoint selection.", "error"))
            return
        removed = self._selected_endpoints.pop(selected_list.cursor_row)
        self._refresh_selected_endpoints_list()
        self.post_message(
            self.StatusMessage(
                f"Endpoint '{removed['endpoint_key']}' removed.",
                "success",
            )
        )

    def _refresh_selected_endpoints_list(self) -> None:
        selected_list = self.query_one("#subscription-selected-endpoints", DataTable)
        selected_list.clear()
        if not self._selected_endpoints:
            selected_list.add_row("-", "No endpoint selected.", "-")
            return
        for endpoint in self._selected_endpoints:
            selected_list.add_row(
                endpoint.get("kind", "-"),
                endpoint.get("endpoint_key", "-"),
                endpoint.get("display", "-"),
            )

    @staticmethod
    def _format_criteria(rule: dict) -> str:
        parts = []
        for criterion in rule.get("criteria", {}).get("all_of", []):
            key = criterion.get("key", "")
            if key == "*" and criterion.get("value") == "*":
                parts.append("(any)")
                continue
            parts.append(
                f"{key} {criterion.get('operator', 'eq')} {criterion.get('value', '')}"
            )
        return ", ".join(parts) if parts else "-"

    def _refresh_list(self) -> None:
        subscriptions_list = self.query_one("#subscriptions-list", DataTable)
        subscriptions_list.clear()
        if not self._subscriptions:
            subscriptions_list.add_row("-", "-", "-", "-", "No subscriptions yet.")
            return
        for item in self._subscriptions:
            subscription = item.get("subscription", {})
            rule = subscription.get("rule", {})
            endpoints_label = ", ".join(
                f"{endpoint.get('kind', '?')}:{endpoint.get('endpoint_key', '?')}"
                for endpoint in subscription.get("endpoints", [])
            )
            subscriptions_list.add_row(
                rule.get("category", "-"),
                rule.get("event_type", "-"),
                self._format_criteria(rule),
                endpoints_label or "-",
                item.get("status", "-"),
            )
