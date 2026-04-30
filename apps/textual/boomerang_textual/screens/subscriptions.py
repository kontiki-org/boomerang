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
    class StatusMessage(Message):
        def __init__(self, text: str, level: str = "info") -> None:
            super().__init__()
            self.text = text
            self.level = level

    def __init__(self) -> None:
        super().__init__()
        self._subscriptions: list[dict[str, str]] = []
        self._alert_capabilities = dict(ALERT_CAPABILITIES)

    def compose(self):
        with Vertical(id="subscriptions-layout"):
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
                table = DataTable(id="subscriptions-list", cursor_type="row")
                table.add_columns(
                    "Category",
                    "Event type",
                    "Criteria",
                    "Status",
                )
                yield table

    def on_mount(self) -> None:
        self._sync_event_type_options()
        self._sync_criterion_key_options()
        self._refresh_list()

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "save-subscription-btn":
            self._handle_save_subscription()
            return
        if event.button.id == "delete-subscription-btn":
            self._handle_delete_selected()

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
        self._sync_criterion_key_options(
            selected_category=selected["category"],
            selected_event_type=selected["event_type"],
            preferred_criterion_key=selected["criterion_key"],
        )
        self.query_one("#subscription-criterion-key", Select).value = selected[
            "criterion_key"
        ]
        self.query_one("#subscription-criterion-operator", Select).value = selected.get(
            "criterion_operator", "eq"
        )
        self.query_one("#subscription-criterion-value", Input).value = selected[
            "criterion_value"
        ]

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

        key = (
            str(category),
            str(event_type),
            str(criterion_key).lower(),
            str(criterion_value).lower(),
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
        self.post_message(self.StatusMessage("Subscription deleted.", "success"))

    def _refresh_list(self) -> None:
        subscriptions_list = self.query_one("#subscriptions-list", DataTable)
        subscriptions_list.clear()
        if not self._subscriptions:
            subscriptions_list.add_row("-", "-", "-", "No subscriptions yet.")
            return
        for item in self._subscriptions:
            subscriptions_list.add_row(
                item["category"],
                item["event_type"],
                f"{item['criterion_key']} {item.get('criterion_operator', 'eq')} {item['criterion_value']}",
                item["status"],
            )
