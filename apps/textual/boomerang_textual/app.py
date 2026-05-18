import os

from kontiki.messaging import Messenger
from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.containers import Container
from textual.widgets import Footer, Header, Static, TabbedContent, TabPane

from boomerang.core.contracts.email_notifier.service import EmailNotifierRpcProxy
from boomerang.core.contracts.identity.service import IdentityRpcProxy
from boomerang.core.contracts.subscription import SubscriptionRpcProxy
from boomerang_textual.screens.auth import AuthScreen
from boomerang_textual.screens.endpoints import EndpointsScreen
from boomerang_textual.screens.subscriptions import SubscriptionsScreen
from boomerang_textual.state.session import SessionState


class HomeView(Container):
    def compose(self) -> ComposeResult:
        yield Static("Welcome to Boomerang Textual.", id="welcome")
        with TabbedContent(initial="subscriptions", id="main-tabs"):
            with TabPane("Subscriptions", id="subscriptions"):
                yield SubscriptionsScreen()
            with TabPane("Endpoints", id="endpoints"):
                yield EndpointsScreen()


class BoomerangTextualApp(App[None]):
    CSS_PATH = "app.css"
    TITLE = "Boomerang Textual"
    SUB_TITLE = "Auth, endpoints, subscriptions"
    BINDINGS = [
        Binding("q", "quit", "Quit", priority=True),
    ]
    session = SessionState()
    messenger: Messenger | None = None
    identity_rpc: IdentityRpcProxy | None = None
    email_notifier_rpc: EmailNotifierRpcProxy | None = None
    subscription_rpc: SubscriptionRpcProxy | None = None

    def compose(self) -> ComposeResult:
        yield Header()
        with Container(id="content"):
            yield AuthScreen()
        yield Container(id="prompt-area")
        yield Footer()

    def on_auth_screen_status_message(self, event: AuthScreen.StatusMessage) -> None:
        self._show_prompt(event.text, event.level)

    def on_auth_screen_auth_succeeded(self, event: AuthScreen.AuthSucceeded) -> None:
        self.session.user_email = event.email
        self.session.access_token = event.access_token
        content = self.query_one("#content", Container)
        content.remove_children()
        content.mount(self._build_home_view())
        self._show_prompt(f"Signed in as {event.email}.", "success")

    def on_endpoints_screen_status_message(self, event: EndpointsScreen.StatusMessage) -> None:
        self._show_prompt(event.text, event.level)

    def on_endpoints_screen_endpoint_catalog_changed(
        self, event: EndpointsScreen.EndpointCatalogChanged
    ) -> None:
        try:
            subscriptions = self.query_one(SubscriptionsScreen)
        except Exception:
            return
        subscriptions.set_available_endpoints(event.endpoints)

    def on_subscriptions_screen_status_message(
        self, event: SubscriptionsScreen.StatusMessage
    ) -> None:
        self._show_prompt(event.text, event.level)

    def _show_prompt(self, text: str, level: str = "info", timeout: float = 4.0) -> None:
        prompt_area = self.query_one("#prompt-area", Container)
        prompt_area.remove_children()
        prompt = Static(text, classes=f"prompt {level}")
        prompt_area.mount(prompt)
        self.set_timer(timeout, prompt.remove)

    async def on_mount(self) -> None:
        amqp_url = os.getenv("BOOMERANG_AMQP_URL", "amqp://guest:guest@localhost/")
        self.messenger = Messenger(amqp_url=amqp_url, standalone=True)
        await self.messenger.setup()
        await self.messenger.start()
        self.identity_rpc = IdentityRpcProxy(self.messenger)
        self.email_notifier_rpc = EmailNotifierRpcProxy(self.messenger)
        self.subscription_rpc = SubscriptionRpcProxy(self.messenger)
        self._show_prompt("Please sign in.", "info", timeout=6.0)

    async def on_unmount(self) -> None:
        if self.messenger is not None:
            await self.messenger.stop()
            self.messenger = None
            self.identity_rpc = None
            self.email_notifier_rpc = None
            self.subscription_rpc = None

    def _build_home_view(self) -> Container:
        return HomeView(id="home-view")

def run() -> None:
    BoomerangTextualApp().run()


if __name__ == "__main__":
    run()
