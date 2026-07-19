import json
import urllib.error
import urllib.request


def base_url() -> str:
    return "http://127.0.0.1:8025"


def purge_messages() -> None:
    request = urllib.request.Request(
        url=f"{base_url()}/api/v1/messages",
        method="DELETE",
    )
    try:
        with urllib.request.urlopen(request, timeout=5):
            return
    except urllib.error.HTTPError as exc:
        # Some MailHog versions return 404 for DELETE; keep tests resilient.
        if exc.code != 404:
            raise


def list_messages() -> list[dict]:
    with urllib.request.urlopen(f"{base_url()}/api/v2/messages", timeout=5) as resp:
        payload = json.loads(resp.read().decode("utf-8"))
    return payload.get("items", []) if isinstance(payload, dict) else []
