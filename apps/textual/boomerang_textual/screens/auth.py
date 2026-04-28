from textual.screen import Screen
from textual.widgets import Static


class AuthScreen(Screen[None]):
    def compose(self):
        yield Static("Auth screen placeholder")

