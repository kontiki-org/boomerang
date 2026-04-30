import re
import secrets

from textual.containers import Container, Horizontal, Vertical
from textual.message import Message
from textual.widgets import Button, Input, Label, Static

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
        with Vertical(id="auth-root"):
            yield Static("Sign in to Boomerang", id="auth-title")
            yield Static(
                "Step 1: enter your email to request a login code.",
                id="auth-step-help",
            )
            with Container(id="email-step"):
                yield Label("Email", classes="field-label")
                yield Input(
                    placeholder="user@example.org",
                    id="email-input",
                )
                yield Button("Send code", id="send-code-btn", variant="primary")
            with Container(id="code-step"):
                yield Static("Step 2: enter the 6-digit code.", id="code-step-help")
                yield Label("Verification code", classes="field-label")
                yield Input(
                    placeholder="123456",
                    id="code-input",
                )
                with Horizontal(id="code-step-actions"):
                    yield Button("Sign in", id="sign-in-btn", variant="success")
                    yield Button("Change email", id="change-email-btn")

    def on_mount(self) -> None:
        code_step = self.query_one("#code-step", Container)
        code_step.display = False
        self.query_one("#email-input", Input).focus()

    def on_button_pressed(self, event: Button.Pressed) -> None:
        button_id = event.button.id
        if button_id == "send-code-btn":
            self._handle_send_code()
            return
        if button_id == "sign-in-btn":
            self._handle_sign_in()
            return
        if button_id == "change-email-btn":
            self._handle_change_email()

    def on_input_submitted(self, event: Input.Submitted) -> None:
        input_id = event.input.id
        if input_id == "email-input":
            self._handle_send_code()
            return
        if input_id == "code-input":
            self._handle_sign_in()

    def _handle_send_code(self) -> None:
        email_input = self.query_one("#email-input", Input)
        raw_email = (email_input.value or "").strip().lower()
        if not EMAIL_RE.match(raw_email):
            self.post_message(
                self.StatusMessage("Please enter a valid email address.", "error")
            )
            return

        self._email_for_code = raw_email
        self.query_one("#code-step", Container).display = True
        self.post_message(
            self.StatusMessage(
                "Verification code requested (mock mode). Check your inbox.",
                "success",
            )
        )
        self.query_one("#code-input", Input).focus()

    def _handle_sign_in(self) -> None:
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

        token = f"local-dev-{secrets.token_hex(8)}"
        self.post_message(self.AuthSucceeded(self._email_for_code, token))

    def _handle_change_email(self) -> None:
        self._email_for_code = None
        self.query_one("#code-step", Container).display = False
        self.query_one("#code-input", Input).value = ""
        self.query_one("#email-input", Input).focus()
        self.post_message(self.StatusMessage("Email reset.", "info"))

