import re

from boomerang.core.contracts.email_notifier import CreateEmailEndpointRequest
from boomerang_textual.api import rpc_error_message
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

    class EndpointCatalogChanged(Message):
        def __init__(self, endpoints: list[dict[str, str]]) -> None:
            super().__init__()
            self.endpoints = endpoints

    def __init__(self) -> None:
        super().__init__()
        self._endpoints: list[dict[str, str]] = []

    def compose(self):
        with Horizontal(id="endpoints-layout"):
            with Vertical(id="endpoints-form-pane"):
                yield Static("Create or update endpoint", classes="section-title")
                yield Label("Endpoint type", classes="field-label")
                yield Select(
                    options=[("Email", "email")],
                    value="email",
                    id="endpoint-kind",
                )
                yield Label("Endpoint key", classes="field-label")
                yield Input(
                    placeholder="endpoint key (example: primary)",
                    id="endpoint-key",
                )
                yield Label("Destination", classes="field-label")
                yield Input(
                    placeholder="email address (example: user@example.org)",
                    id="endpoint-address",
                )
                with Horizontal(id="endpoints-form-actions"):
                    yield Button("Save endpoint", id="save-endpoint-btn", variant="primary")
                    yield Button("Delete selected", id="delete-endpoint-btn", variant="error")
            with Vertical(id="endpoints-list-pane"):
                yield Static("Registered endpoints", classes="section-title")
                table = DataTable(id="endpoints-list", cursor_type="row")
                table.add_columns("Type", "Endpoint key", "Destination")
                yield table

    async def on_mount(self) -> None:
        await self._reload_endpoints()

    async def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "save-endpoint-btn":
            await self._handle_save_endpoint()
            return
        if event.button.id == "delete-endpoint-btn":
            await self._handle_delete_selected()

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

    def _auth_headers(self) -> dict[str, str] | None:
        token = self.app.session.access_token  # type: ignore[attr-defined]
        if not token:
            return None
        return {"Authorization": f"Bearer {token}"}

    def _sync_table(self) -> None:
        self._refresh_list()
        self._publish_endpoint_catalog()

    async def _reload_endpoints(self) -> None:
        headers = self._auth_headers()
        if headers is None:
            self._endpoints = []
            self._sync_table()
            return

        try:
            result = await self.app.email_notifier_rpc.list_email_endpoints(  # type: ignore[attr-defined]
                extra_headers=headers
            )
        except Exception as exc:
            self.post_message(self.StatusMessage(rpc_error_message(exc), "error"))
            self._endpoints = []
            self._sync_table()
            return

        self._endpoints = [
            {
                "kind": "email",
                "endpoint_key": e["endpoint_key"],
                "address": e["address"],
            }
            for e in result["endpoints"]
        ]
        self._sync_table()

    async def _handle_save_endpoint(self) -> None:
        kind_select = self.query_one("#endpoint-kind", Select)
        key_input = self.query_one("#endpoint-key", Input)
        address_input = self.query_one("#endpoint-address", Input)
        endpoint_kind = str(kind_select.value or "email")
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

        headers = self._auth_headers()
        if headers is None:
            self.post_message(self.StatusMessage("Not signed in.", "error"))
            return

        try:
            body = CreateEmailEndpointRequest(
                endpoint_key=endpoint_key, address=address
            )
            await self.app.email_notifier_rpc.create_email_endpoint(  # type: ignore[attr-defined]
                body=body,
                extra_headers=headers,
            )
        except Exception as exc:
            self.post_message(self.StatusMessage(rpc_error_message(exc), "error"))
            return

        key_input.value = ""
        address_input.value = ""
        await self._reload_endpoints()
        self.post_message(
            self.StatusMessage(f"Email endpoint '{endpoint_key}' saved.", "success")
        )

    async def _handle_delete_selected(self) -> None:
        endpoints_list = self.query_one("#endpoints-list", DataTable)
        if endpoints_list.cursor_row is None or endpoints_list.cursor_row < 0:
            self.post_message(self.StatusMessage("No endpoint selected.", "error"))
            return
        if endpoints_list.cursor_row >= len(self._endpoints):
            self.post_message(self.StatusMessage("Invalid selection.", "error"))
            return

        endpoint_key = self._endpoints[endpoints_list.cursor_row]["endpoint_key"]
        headers = self._auth_headers()
        if headers is None:
            self.post_message(self.StatusMessage("Not signed in.", "error"))
            return

        try:
            await self.app.email_notifier_rpc.delete_email_endpoint(  # type: ignore[attr-defined]
                endpoint_key=endpoint_key,
                extra_headers=headers,
            )
        except Exception as exc:
            self.post_message(self.StatusMessage(rpc_error_message(exc), "error"))
            return

        await self._reload_endpoints()
        self.post_message(
            self.StatusMessage(f"Endpoint '{endpoint_key}' deleted.", "success")
        )

    def _refresh_list(self) -> None:
        endpoints_list = self.query_one("#endpoints-list", DataTable)
        endpoints_list.clear()
        if not self._endpoints:
            endpoints_list.add_row("-", "No endpoints yet.", "-")
            return
        for item in self._endpoints:
            endpoints_list.add_row(item["kind"], item["endpoint_key"], item["address"])

    def _publish_endpoint_catalog(self) -> None:
        endpoints = sorted(
            [
                {
                    "kind": item["kind"],
                    "endpoint_key": item["endpoint_key"],
                    "address": item["address"],
                }
                for item in self._endpoints
            ],
            key=lambda item: (item["kind"], item["endpoint_key"]),
        )
        self.post_message(self.EndpointCatalogChanged(endpoints))
