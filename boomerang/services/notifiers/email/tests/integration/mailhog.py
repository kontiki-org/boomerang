import json
import quopri
import urllib.error
import urllib.request


def base_url():
    return "http://127.0.0.1:8025"


def purge_messages():
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


def list_messages():
    with urllib.request.urlopen(f"{base_url()}/api/v2/messages", timeout=5) as resp:
        payload = json.loads(resp.read().decode("utf-8"))
    return payload.get("items", []) if isinstance(payload, dict) else []


def searchable_body(message):
    """Plain + decoded MIME parts (quoted-printable soft breaks removed)."""
    chunks = []
    content = message.get("Content") or {}
    raw = content.get("Body") or ""
    if raw:
        chunks.append(raw)

    mime = message.get("MIME") or {}
    for part in mime.get("Parts") or []:
        body = part.get("Body") or ""
        if not body:
            continue
        headers = part.get("Headers") or {}
        cte_values = headers.get("Content-Transfer-Encoding") or []
        cte = cte_values[0].lower() if cte_values else ""
        if "quoted-printable" in cte:
            body = quopri.decodestring(body.encode("latin-1")).decode(
                "utf-8", errors="replace"
            )
        chunks.append(body)
    return "\n".join(chunks)
