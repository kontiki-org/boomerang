from textual.app import App, ComposeResult
from textual.containers import Container
from textual.widgets import Footer, Header, ListItem, ListView, Static


class BoomerangTextualApp(App[None]):
    TITLE = "Boomerang Textual"
    SUB_TITLE = "Auth, endpoints, subscriptions"

    def compose(self) -> ComposeResult:
        yield Header()
        with Container():
            yield Static("Welcome to Boomerang Textual.", id="welcome")
            yield ListView(
                ListItem(Static("Auth flow")),
                ListItem(Static("Endpoints")),
                ListItem(Static("Subscriptions")),
                id="main-menu",
            )
        yield Footer()


def run() -> None:
    BoomerangTextualApp().run()


if __name__ == "__main__":
    run()

