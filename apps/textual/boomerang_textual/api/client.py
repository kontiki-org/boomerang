from dataclasses import dataclass

import httpx


@dataclass
class BoomerangApiClient:
    identity_base_url: str = "http://127.0.0.1:8001"
    subscription_base_url: str = "http://127.0.0.1:8002"
    email_notifier_base_url: str = "http://127.0.0.1:8003"

    def request_auth_code(self, email: str) -> dict:
        response = httpx.post(
            f"{self.identity_base_url}/auth/request-auth-code",
            json={"email": email},
            timeout=10,
        )
        response.raise_for_status()
        return response.json()

