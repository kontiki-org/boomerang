import re

from textual.containers import Container, Horizontal, Vertical
from textual.message import Message
from textual.widgets import Button, Input, Static

EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
CODE_RE = re.compile(r"^\d{6}$")


class AuthScreen(Static):
    class StatusMessage(Message):
        def __init__(self, text: str, level: str = "info") -> None:
            super().__init__()
            self.text = text
            self.level = level

    class AuthSucceeded(Message):
        def __init__(self, email: str, access_token: str) -> None:
            super().__init__()
            self.email = email
            self.access_token = access_token

    def __init__(self) -> None:
        super().__init__()
        self._email_for_code: str | None = None

    def compose(self):
        with Container(id="auth-shell"):
            with Vertical(id="auth-root"):
                with Container(id="email-step"):
                    yield Input(
                        placeholder="user@example.org",
                        id="email-input",
                    )
                    yield Button("Send code", id="send-code-btn", variant="primary")
                with Container(id="code-step"):
                    yield Input(
                        placeholder="Enter the 6-digit code.",
                        id="code-input",
                    )
                    with Horizontal(id="code-step-actions"):
                        yield Button("Sign in", id="sign-in-btn", variant="success")
                        yield Button("Change email", id="change-email-btn")

    def on_mount(self) -> None:
        self.query_one("#auth-root", Vertical).border_title = "Sign in to Boomerang"
        self._set_code_step_enabled(False)
        self.query_one("#email-input", Input).focus()

    async def on_button_pressed(self, event: Button.Pressed) -> None:
        button_id = event.button.id
        if button_id == "send-code-btn":
            await self._handle_send_code()
            return
        if button_id == "sign-in-btn":
            await self._handle_sign_in()
            return
        if button_id == "change-email-btn":
            self._handle_change_email()

    async def on_input_submitted(self, event: Input.Submitted) -> None:
        input_id = event.input.id
        if input_id == "email-input":
            await self._handle_send_code()
            return
        if input_id == "code-input":
            await self._handle_sign_in()

    async def _handle_send_code(self) -> None:
        email_input = self.query_one("#email-input", Input)
        raw_email = (email_input.value or "").strip().lower()
        if not EMAIL_RE.match(raw_email):
            self.post_message(
                self.StatusMessage("Please enter a valid email address.", "error")
            )
            return

        identity_rpc = self.app.identity_rpc  # type: ignore[attr-defined]
        if identity_rpc is None:
            self.post_message(
                self.StatusMessage("Identity service is not connected.", "error")
            )
            return

        try:
            await identity_rpc.request_auth_code(email=raw_email)
        except Exception as exc:
            self.post_message(self.StatusMessage(self._to_user_error(exc), "error"))
            return

        self._email_for_code = raw_email
        self._set_code_step_enabled(True)
        self.post_message(self.StatusMessage("Verification code sent.", "success"))
        self.query_one("#code-input", Input).focus()

    async def _handle_sign_in(self) -> None:
        if not self._email_for_code:
            self.post_message(
                self.StatusMessage("Please request a code first.", "error")
            )
            return

        code = (self.query_one("#code-input", Input).value or "").strip()
        if not CODE_RE.match(code):
            self.post_message(
                self.StatusMessage("Code must contain exactly 6 digits.", "error")
            )
            return

        identity_rpc = self.app.identity_rpc  # type: ignore[attr-defined]
        if identity_rpc is None:
            self.post_message(
                self.StatusMessage("Identity service is not connected.", "error")
            )
            return

        try:
            payload = await identity_rpc.consume_auth_code(code=code)
        except Exception as exc:
            self.post_message(self.StatusMessage(self._to_user_error(exc), "error"))
            return

        access_token = payload.get("access_token")
        if not isinstance(access_token, str) or not access_token.strip():
            self.post_message(
                self.StatusMessage("Invalid auth response from backend.", "error")
            )
            return
        self.post_message(self.AuthSucceeded(self._email_for_code, access_token))

    def _handle_change_email(self) -> None:
        self._email_for_code = None
        self._set_code_step_enabled(False)
        self.query_one("#code-input", Input).value = ""
        self.query_one("#email-input", Input).focus()
        self.post_message(self.StatusMessage("Email reset.", "info"))

    def _set_code_step_enabled(self, enabled: bool) -> None:
        self.query_one("#code-input", Input).disabled = not enabled
        self.query_one("#sign-in-btn", Button).disabled = not enabled
        self.query_one("#change-email-btn", Button).disabled = not enabled

    @staticmethod
    def _to_user_error(exc: Exception) -> str:
        error_code = ""
        try:
            code_value = exc.code  # type: ignore[attr-defined]
            if isinstance(code_value, str):
                error_code = code_value.strip().upper()
        except AttributeError:
            pass
        if error_code == "AUTH_ERROR":
            return "Invalid or expired verification code."
        if error_code == "VALIDATION_ERROR":
            return "Provided authentication data is invalid."
        if error_code == "RATE_LIMIT_ERROR":
            return "Too many attempts. Please wait and try again."
        if error_code == "DEPENDENCY_ERROR":
            return "Identity service dependency is unavailable."
        if error_code == "INTERNAL_ERROR":
            return "Provided authentication data is invalid."
        try:
            message_value = exc.message  # type: ignore[attr-defined]
            if isinstance(message_value, str) and message_value.strip():
                return message_value
        except AttributeError:
            pass
        return "Identity service is unreachable."
