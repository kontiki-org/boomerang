from boomerang_textual.api import rpc_error_message
from boomerang_textual.api.channel_catalog import (
    ChannelCatalogIndex,
    build_channel_catalog_index,
    channel_catalog_from_rpc,
)
from textual.containers import Horizontal, Vertical
from textual.message import Message
from textual.widgets import Button, DataTable, Input, Label, Select, Static

from boomerang_contracts.notification.endpoint import CreateChannelEndpointRequest
from boomerang_contracts.notification.validation import validate_endpoint_fields


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
        self._catalog_index: ChannelCatalogIndex | None = None
        self._suppress_kind_select_rebuild = False

    def compose(self):
        with Horizontal(id="endpoints-layout"):
            with Vertical(id="endpoints-form-pane"):
                yield Static("Create or update endpoint", classes="section-title")
                yield Label("Endpoint type", classes="field-label")
                yield Select(options=[], id="endpoint-kind")
                yield Label("Endpoint key", classes="field-label")
                yield Input(
                    placeholder="endpoint key (example: primary)",
                    id="endpoint-key",
                )
                with Vertical(id="endpoint-fields"):
                    pass
                with Horizontal(id="endpoints-form-actions"):
                    yield Button(
                        "Save endpoint", id="save-endpoint-btn", variant="primary"
                    )
                    yield Button(
                        "Delete selected", id="delete-endpoint-btn", variant="error"
                    )
            with Vertical(id="endpoints-list-pane"):
                yield Static("Registered endpoints", classes="section-title")
                table = DataTable(id="endpoints-list", cursor_type="row")
                table.add_columns("Type", "Endpoint key", "Destination")
                yield table

    async def on_mount(self) -> None:
        await self._load_catalog()
        await self._reload_endpoints()

    async def on_select_changed(self, event: Select.Changed) -> None:
        if event.select.id != "endpoint-kind":
            return
        if self._suppress_kind_select_rebuild:
            return
        await self._rebuild_field_inputs()

    async def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "save-endpoint-btn":
            await self._handle_save_endpoint()
            return
        if event.button.id == "delete-endpoint-btn":
            await self._handle_delete_selected()

    async def on_data_table_row_selected(self, event: DataTable.RowSelected) -> None:
        if event.data_table.id != "endpoints-list":
            return
        if event.cursor_row is None or event.cursor_row < 0:
            return
        if event.cursor_row >= len(self._endpoints):
            return
        selected = self._endpoints[event.cursor_row]
        kind_select = self.query_one("#endpoint-kind", Select)
        self._suppress_kind_select_rebuild = True
        kind_select.value = selected["kind"]
        self._suppress_kind_select_rebuild = False
        await self._rebuild_field_inputs()
        self.query_one("#endpoint-key", Input).value = selected["endpoint_key"]
        for field_key, value in selected.get("fields", {}).items():
            field_input = self.query_one(f"#endpoint-field-{field_key}", Input)
            field_input.value = value

    def _auth_headers(self) -> dict[str, str] | None:
        token = self.app.session.access_token  # type: ignore[attr-defined]
        if not token:
            return None
        return {"Authorization": f"Bearer {token}"}

    def _sync_table(self) -> None:
        self._refresh_list()
        self._publish_endpoint_catalog()

    async def _load_catalog(self) -> None:
        try:
            raw = await self.app.subscription_rpc.get_notification_channels_catalog()  # type: ignore[attr-defined]
        except Exception as exc:
            self.post_message(self.StatusMessage(rpc_error_message(exc), "error"))
            self._catalog_index = ChannelCatalogIndex()
            return

        catalog = channel_catalog_from_rpc(raw)
        self._catalog_index = build_channel_catalog_index(catalog)
        kind_select = self.query_one("#endpoint-kind", Select)
        if self._catalog_index.channels:
            kind_select.set_options(self._catalog_index.channels)
            self._suppress_kind_select_rebuild = True
            kind_select.value = self._catalog_index.channels[0][1]
            self._suppress_kind_select_rebuild = False
        else:
            kind_select.set_options([("No channel available", "")])
            self._suppress_kind_select_rebuild = True
            kind_select.value = ""
            self._suppress_kind_select_rebuild = False
        await self._rebuild_field_inputs()

    def _selected_channel(self):
        if self._catalog_index is None:
            return None
        channel_id = str(self.query_one("#endpoint-kind", Select).value or "").strip()
        if not channel_id:
            return None
        return self._catalog_index.channel_by_id.get(channel_id)

    async def _rebuild_field_inputs(self) -> None:
        fields_container = self.query_one("#endpoint-fields", Vertical)
        await fields_container.remove_children()
        channel = self._selected_channel()
        if channel is None:
            return
        for descriptor in channel.fields:
            await fields_container.mount(Label(descriptor.label, classes="field-label"))
            password = descriptor.field_type == "secret"
            await fields_container.mount(
                Input(
                    placeholder=descriptor.placeholder or "",
                    id=f"endpoint-field-{descriptor.key}",
                    password=password,
                )
            )

    def _collect_fields(self, channel) -> dict[str, str]:
        collected = {}
        for descriptor in channel.fields:
            field_input = self.query_one(f"#endpoint-field-{descriptor.key}", Input)
            collected[descriptor.key] = (field_input.value or "").strip()
        return collected

    async def _reload_endpoints(self) -> None:
        headers = self._auth_headers()
        if headers is None:
            self._endpoints = []
            self._sync_table()
            return

        try:
            result = await self.app.subscription_rpc.list_endpoints(  # type: ignore[attr-defined]
                extra_headers=headers
            )
        except Exception as exc:
            self.post_message(self.StatusMessage(rpc_error_message(exc), "error"))
            self._endpoints = []
            self._sync_table()
            return

        self._endpoints = [
            {
                "kind": endpoint["channel_id"],
                "endpoint_key": endpoint["endpoint_key"],
                "display": endpoint.get("display", ""),
                "fields": endpoint.get("fields", {}),
            }
            for endpoint in result.get("endpoints", [])
        ]
        self._sync_table()

    async def _handle_save_endpoint(self) -> None:
        channel = self._selected_channel()
        key_input = self.query_one("#endpoint-key", Input)
        endpoint_key = (key_input.value or "").strip()

        if channel is None:
            self.post_message(
                self.StatusMessage("No notification channel available.", "error")
            )
            return
        if not endpoint_key:
            self.post_message(self.StatusMessage("Endpoint key is required.", "error"))
            return

        fields = self._collect_fields(channel)
        try:
            validate_endpoint_fields(channel, fields)
        except Exception:
            self.post_message(
                self.StatusMessage("Please check the endpoint field values.", "error")
            )
            return

        headers = self._auth_headers()
        if headers is None:
            self.post_message(self.StatusMessage("Not signed in.", "error"))
            return

        try:
            body = CreateChannelEndpointRequest(
                channel_id=channel.channel_id,
                endpoint_key=endpoint_key,
                fields=fields,
            )
            await self.app.subscription_rpc.create_endpoint(  # type: ignore[attr-defined]
                body=body,
                extra_headers=headers,
            )
        except Exception as exc:
            self.post_message(self.StatusMessage(rpc_error_message(exc), "error"))
            return

        key_input.value = ""
        await self._rebuild_field_inputs()
        await self._reload_endpoints()
        self.post_message(
            self.StatusMessage(
                f"{channel.label} endpoint '{endpoint_key}' saved.",
                "success",
            )
        )

    async def _handle_delete_selected(self) -> None:
        endpoints_list = self.query_one("#endpoints-list", DataTable)
        if endpoints_list.cursor_row is None or endpoints_list.cursor_row < 0:
            self.post_message(self.StatusMessage("No endpoint selected.", "error"))
            return
        if endpoints_list.cursor_row >= len(self._endpoints):
            self.post_message(self.StatusMessage("Invalid selection.", "error"))
            return

        selected = self._endpoints[endpoints_list.cursor_row]
        headers = self._auth_headers()
        if headers is None:
            self.post_message(self.StatusMessage("Not signed in.", "error"))
            return

        try:
            await self.app.subscription_rpc.delete_endpoint(  # type: ignore[attr-defined]
                channel_id=selected["kind"],
                endpoint_key=selected["endpoint_key"],
                extra_headers=headers,
            )
        except Exception as exc:
            self.post_message(self.StatusMessage(rpc_error_message(exc), "error"))
            return

        await self._reload_endpoints()
        self.post_message(
            self.StatusMessage(
                f"Endpoint '{selected['endpoint_key']}' deleted.", "success"
            )
        )

    def _refresh_list(self) -> None:
        endpoints_list = self.query_one("#endpoints-list", DataTable)
        endpoints_list.clear()
        if not self._endpoints:
            endpoints_list.add_row("-", "No endpoints yet.", "-")
            return
        for item in self._endpoints:
            kind = item["kind"]
            label = kind
            if self._catalog_index is not None:
                channel = self._catalog_index.channel_by_id.get(kind)
                if channel is not None:
                    label = channel.label
            endpoints_list.add_row(
                label, item["endpoint_key"], item.get("display", "-")
            )

    def _publish_endpoint_catalog(self) -> None:
        endpoints = sorted(
            [
                {
                    "kind": item["kind"],
                    "endpoint_key": item["endpoint_key"],
                    "display": item.get("display", ""),
                    "fields": item.get("fields", {}),
                }
                for item in self._endpoints
            ],
            key=lambda item: (item["kind"], item["endpoint_key"]),
        )
        self.post_message(self.EndpointCatalogChanged(endpoints))
