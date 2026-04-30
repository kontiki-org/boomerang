import re

from textual.containers import Horizontal, Vertical
from textual.message import Message
from textual.widgets import Button, DataTable, Input, Label, Select, Static

EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


class EndpointsScreen(Static):
    class StatusMessage(Message):
        def __init__(self, text: str, level: str = "info") -> None:
            super().__init__()
            self.text = text
            self.level = level

    class EndpointKeysChanged(Message):
        def __init__(self, endpoint_keys: list[str]) -> None:
            super().__init__()
            self.endpoint_keys = endpoint_keys

    def __init__(self) -> None:
        super().__init__()
        self._endpoints: list[dict[str, str]] = []

    def compose(self):
        with Vertical(id="endpoints-layout"):
            with Vertical(id="endpoints-form-pane"):
                yield Static("Create or update endpoint", classes="section-title")
                yield Label("Endpoint type", classes="field-label")
                yield Select(
                    options=[("Email", "email")],
                    value="email",
                    id="endpoint-kind",
                )
                yield Label("Endpoint key", classes="field-label")
                yield Input(placeholder="endpoint key (example: primary)", id="endpoint-key")
                yield Label("Destination", classes="field-label")
                yield Input(
                    placeholder="email address (example: user@example.org)",
                    id="endpoint-address",
                )
                with Horizontal(id="endpoints-form-actions"):
                    yield Button("Save endpoint", id="save-endpoint-btn", variant="primary")
                    yield Button("Delete selected", id="delete-endpoint-btn", variant="error")
            with Vertical(id="endpoints-list-pane"):
                table = DataTable(id="endpoints-list", cursor_type="row")
                table.add_columns("Type", "Endpoint key", "Destination")
                yield table

    def on_mount(self) -> None:
        self._refresh_list()
        self._publish_endpoint_keys()

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "save-endpoint-btn":
            self._handle_save_endpoint()
            return
        if event.button.id == "delete-endpoint-btn":
            self._handle_delete_selected()

    def on_data_table_row_selected(self, event: DataTable.RowSelected) -> None:
        if event.data_table.id != "endpoints-list":
            return
        if event.cursor_row is None or event.cursor_row < 0:
            return
        if event.cursor_row >= len(self._endpoints):
            return
        selected = self._endpoints[event.cursor_row]
        self.query_one("#endpoint-kind", Select).value = selected["kind"]
        self.query_one("#endpoint-key", Input).value = selected["endpoint_key"]
        self.query_one("#endpoint-address", Input).value = selected["address"]

    def _handle_save_endpoint(self) -> None:
        kind_select = self.query_one("#endpoint-kind", Select)
        key_input = self.query_one("#endpoint-key", Input)
        address_input = self.query_one("#endpoint-address", Input)
        endpoint_kind = kind_select.value or "email"
        endpoint_key = (key_input.value or "").strip()
        address = (address_input.value or "").strip().lower()

        if not endpoint_key:
            self.post_message(self.StatusMessage("Endpoint key is required.", "error"))
            return
        if endpoint_kind == "email" and not EMAIL_RE.match(address):
            self.post_message(self.StatusMessage("Please enter a valid email address.", "error"))
            return
        if endpoint_kind != "email":
            self.post_message(
                self.StatusMessage(
                    f"Endpoint type '{endpoint_kind}' is not supported yet.",
                    "error",
                )
            )
            return

        existing = next(
            (
                item
                for item in self._endpoints
                if item["endpoint_key"] == endpoint_key and item["kind"] == endpoint_kind
            ),
            None,
        )
        if existing is None:
            self._endpoints.append(
                {"kind": endpoint_kind, "endpoint_key": endpoint_key, "address": address}
            )
            message = f"{endpoint_kind} endpoint '{endpoint_key}' created."
        else:
            existing["address"] = address
            message = f"{endpoint_kind} endpoint '{endpoint_key}' updated."

        key_input.value = ""
        address_input.value = ""
        self._refresh_list()
        self._publish_endpoint_keys()
        self.post_message(self.StatusMessage(message, "success"))

    def _handle_delete_selected(self) -> None:
        endpoints_list = self.query_one("#endpoints-list", DataTable)
        if endpoints_list.cursor_row is None or endpoints_list.cursor_row < 0:
            self.post_message(self.StatusMessage("No endpoint selected.", "error"))
            return
        if endpoints_list.cursor_row >= len(self._endpoints):
            self.post_message(self.StatusMessage("Invalid selection.", "error"))
            return

        deleted = self._endpoints.pop(endpoints_list.cursor_row)
        self._refresh_list()
        self._publish_endpoint_keys()
        self.post_message(
            self.StatusMessage(
                f"Endpoint '{deleted['endpoint_key']}' deleted.",
                "success",
            )
        )

    def _refresh_list(self) -> None:
        endpoints_list = self.query_one("#endpoints-list", DataTable)
        endpoints_list.clear()
        if not self._endpoints:
            endpoints_list.add_row("-", "No endpoints yet.", "-")
            return
        for item in self._endpoints:
            endpoints_list.add_row(item["kind"], item["endpoint_key"], item["address"])

    def _publish_endpoint_keys(self) -> None:
        keys = sorted(
            {
                item["endpoint_key"]
                for item in self._endpoints
                if item.get("kind") == "email"
            }
        )
        self.post_message(self.EndpointKeysChanged(keys))

