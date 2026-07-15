from dataclasses import dataclass


@dataclass
class SessionState:
    access_token: str | None = None
    user_email: str | None = None

    @property
    def is_authenticated(self) -> bool:
        return bool(self.access_token)
