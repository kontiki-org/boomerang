from textual.containers import Horizontal, Vertical
from textual.message import Message
from textual.widgets import Button, DataTable, Input, Label, Select, Static

ALERT_CAPABILITIES: dict[str, list[str]] = {
    "weather.alert": ["wind", "rain"],
    "natural.earthquake": ["earthquake"],
}
CRITERIA_CAPABILITIES: dict[str, dict[str, list[str]]] = {
    "weather.alert": {
        "wind": ["min_severity", "area.region", "area.country"],
        "rain": ["min_severity", "rainfall_mm", "area.region"],
    },
    "natural.earthquake": {
        "earthquake": ["min_magnitude", "area.region", "distance_km"],
    },
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
        self._alert_capabilities = dict(ALERT_CAPABILITIES)
        self._available_endpoints: list[dict[str, str]] = []
        self._selected_endpoints: list[dict[str, str]] = []

    def compose(self):
        with Horizontal(id="subscriptions-layout"):
            with Vertical(id="subscriptions-form-pane"):
                yield Static("Create or update subscription", classes="section-title")
                with Horizontal(id="subscriptions-form-line-1"):
                    with Vertical(classes="field-group"):
                        yield Label("Alert category", classes="field-label")
                        yield Select(
                            options=[
                                (label, value)
                                for label, value in [
                                    ("weather.alert", "weather.alert"),
                                    ("natural.earthquake", "natural.earthquake"),
                                ]
                            ],
                            value="weather.alert",
                            id="subscription-category",
                        )
                    with Vertical(classes="field-group"):
                        yield Label("Event type", classes="field-label")
                        yield Select(
                            options=[("wind", "wind"), ("rain", "rain")],
                            value="wind",
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
                            options=[
                                ("equals", "eq"),
                                ("greater or equal", "gte"),
                                ("less or equal", "lte"),
                                ("contains", "contains"),
                            ],
                            value="eq",
                            id="subscription-criterion-operator",
                        )
                    with Vertical(classes="field-group"):
                        yield Label("Criterion value (optional)", classes="field-label")
                        yield Input(
                            placeholder="example: severe / FR-ARA / 5.0",
                            id="subscription-criterion-value",
                        )
                with Horizontal(id="subscriptions-form-line-3"):
                    with Vertical(classes="field-group"):
                        yield Label("Endpoint to add", classes="field-label")
                        yield Select(
                            options=[("No endpoint available", self.EMPTY_ENDPOINT_VALUE)],
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

    def on_mount(self) -> None:
        self._sync_event_type_options()
        self._sync_criterion_key_options()
        self._sync_endpoint_select_options()
        self._refresh_selected_endpoints_list()
        self._refresh_list()

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "save-subscription-btn":
            self._handle_save_subscription()
            return
        if event.button.id == "delete-subscription-btn":
            self._handle_delete_selected()
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
        selected = self._subscriptions[event.cursor_row]
        self.query_one("#subscription-category", Select).value = selected["category"]
        self._sync_event_type_options(
            selected_category=selected["category"],
            preferred_event_type=selected["event_type"],
        )
        self.query_one("#subscription-event-type", Select).value = selected["event_type"]
        preferred_criterion_key = selected["criterion_key"]
        if preferred_criterion_key == "*":
            preferred_criterion_key = self.EMPTY_CRITERION_KEY
        self._sync_criterion_key_options(
            selected_category=selected["category"],
            selected_event_type=selected["event_type"],
            preferred_criterion_key=preferred_criterion_key,
        )
        self.query_one("#subscription-criterion-key", Select).value = preferred_criterion_key
        self.query_one("#subscription-criterion-operator", Select).value = selected.get(
            "criterion_operator", "eq"
        )
        self.query_one("#subscription-criterion-value", Input).value = selected[
            "criterion_value"
        ]
        self._selected_endpoints = list(selected.get("endpoints", []))
        self._refresh_selected_endpoints_list()

    def on_select_changed(self, event: Select.Changed) -> None:
        if event.select.id == "subscription-category":
            selected_category = event.value if isinstance(event.value, str) else ""
            self._sync_event_type_options(selected_category=selected_category)
            self._sync_criterion_key_options(selected_category=selected_category)
        elif event.select.id == "subscription-event-type":
            selected_event_type = event.value if isinstance(event.value, str) else ""
            self._sync_criterion_key_options(selected_event_type=selected_event_type)

    def _sync_event_type_options(
        self,
        selected_category: str | None = None,
        preferred_event_type: str | None = None,
    ) -> None:
        category_select = self.query_one("#subscription-category", Select)
        event_select = self.query_one("#subscription-event-type", Select)
        category = selected_category or category_select.value or "weather.alert"
        available = self._alert_capabilities.get(str(category), [])
        if not available:
            available = ["unknown"]
        event_select.set_options([(item, item) for item in available])
        if preferred_event_type in available:
            event_select.value = preferred_event_type
        else:
            event_select.value = available[0]

    def _sync_criterion_key_options(
        self,
        selected_category: str | None = None,
        selected_event_type: str | None = None,
        preferred_criterion_key: str | None = None,
    ) -> None:
        category_select = self.query_one("#subscription-category", Select)
        event_select = self.query_one("#subscription-event-type", Select)
        criterion_select = self.query_one("#subscription-criterion-key", Select)
        category = selected_category or category_select.value or "weather.alert"
        event_type = selected_event_type or event_select.value or "wind"
        available = CRITERIA_CAPABILITIES.get(str(category), {}).get(str(event_type), [])
        options = [("No criterion", self.EMPTY_CRITERION_KEY)] + [
            (item, item) for item in available
        ]
        criterion_select.set_options(options)
        if preferred_criterion_key and preferred_criterion_key in available:
            criterion_select.value = preferred_criterion_key
        else:
            criterion_select.value = self.EMPTY_CRITERION_KEY

    def _handle_save_subscription(self) -> None:
        category = self.query_one("#subscription-category", Select).value or ""
        event_type = self.query_one("#subscription-event-type", Select).value or ""
        criterion_key = self.query_one("#subscription-criterion-key", Select).value or ""
        criterion_operator = (
            self.query_one("#subscription-criterion-operator", Select).value or "eq"
        )
        criterion_value = (
            self.query_one("#subscription-criterion-value", Input).value or ""
        ).strip()
        status = "active"

        if criterion_key == self.EMPTY_CRITERION_KEY:
            criterion_key = ""
        if bool(criterion_key) != bool(criterion_value):
            self.post_message(
                self.StatusMessage(
                    "Criterion key and value must be provided together.",
                    "error",
                )
            )
            return
        if not criterion_key:
            criterion_key = "*"
            criterion_operator = "eq"
            criterion_value = "*"
        if not self._selected_endpoints:
            self.post_message(
                self.StatusMessage(
                    "Please add at least one endpoint from the Endpoints tab.",
                    "error",
                )
            )
            return

        key = (
            str(category),
            str(event_type),
            str(criterion_key).lower(),
            str(criterion_operator).lower(),
            str(criterion_value).lower(),
            tuple(
                sorted(
                    (
                        endpoint["kind"],
                        endpoint["endpoint_key"],
                    )
                    for endpoint in self._selected_endpoints
                )
            ),
        )
        existing = next(
            (
                item
                for item in self._subscriptions
                if (
                    item["category"],
                    item["event_type"],
                    item["criterion_key"],
                    item["criterion_operator"],
                    item["criterion_value"],
                    tuple(
                        sorted(
                            (
                                endpoint["kind"],
                                endpoint["endpoint_key"],
                            )
                            for endpoint in item.get("endpoints", [])
                        )
                    ),
                )
                == key
            ),
            None,
        )

        payload = {
            "category": str(category),
            "event_type": str(event_type),
            "criterion_key": str(criterion_key).lower(),
            "criterion_operator": str(criterion_operator).lower(),
            "criterion_value": str(criterion_value).lower(),
            "endpoints": [dict(endpoint) for endpoint in self._selected_endpoints],
            "status": str(status),
        }

        if existing is None:
            self._subscriptions.append(payload)
            message = "Subscription created."
        else:
            payload["status"] = existing.get("status", "active")
            existing.update(payload)
            message = "Subscription updated."

        self._refresh_list()
        self._selected_endpoints = []
        self._refresh_selected_endpoints_list()
        self.post_message(self.StatusMessage(message, "success"))

    def _handle_delete_selected(self) -> None:
        subscriptions_list = self.query_one("#subscriptions-list", DataTable)
        if subscriptions_list.cursor_row is None or subscriptions_list.cursor_row < 0:
            self.post_message(self.StatusMessage("No subscription selected.", "error"))
            return
        if subscriptions_list.cursor_row >= len(self._subscriptions):
            self.post_message(self.StatusMessage("Invalid selection.", "error"))
            return
        self._subscriptions.pop(subscriptions_list.cursor_row)
        self._refresh_list()
        self._selected_endpoints = []
        self._refresh_selected_endpoints_list()
        self.post_message(self.StatusMessage("Subscription deleted.", "success"))

    def set_available_endpoints(self, endpoints: list[dict[str, str]]) -> None:
        self._available_endpoints = list(endpoints)
        self._sync_endpoint_select_options()

    def _sync_endpoint_select_options(self) -> None:
        endpoint_select = self.query_one("#subscription-endpoint-select", Select)
        options = []
        for endpoint in self._available_endpoints:
            kind = endpoint.get("kind", "").strip().lower()
            endpoint_key = endpoint.get("endpoint_key", "").strip()
            address = endpoint.get("address", "").strip()
            if not kind or not endpoint_key:
                continue
            label = f"{kind} | {endpoint_key} | {address or '-'}"
            value = f"{kind}:{endpoint_key}"
            options.append((label, value))
        if not options:
            endpoint_select.set_options([("No endpoint available", self.EMPTY_ENDPOINT_VALUE)])
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
                "address": endpoint.get("address", ""),
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
                endpoint.get("address", "-"),
            )

    def _refresh_list(self) -> None:
        subscriptions_list = self.query_one("#subscriptions-list", DataTable)
        subscriptions_list.clear()
        if not self._subscriptions:
            subscriptions_list.add_row("-", "-", "-", "-", "No subscriptions yet.")
            return
        for item in self._subscriptions:
            endpoints_label = ", ".join(
                f"{endpoint.get('kind', '?')}:{endpoint.get('endpoint_key', '?')}"
                for endpoint in item.get("endpoints", [])
            )
            subscriptions_list.add_row(
                item["category"],
                item["event_type"],
                f"{item['criterion_key']} {item.get('criterion_operator', 'eq')} {item['criterion_value']}",
                endpoints_label or "-",
                item["status"],
            )
