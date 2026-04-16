from boomerang.testing import http_request, start_kontiki_subprocess


def start_subscription_subprocess(config):
    return start_kontiki_subprocess(
        "boomerang.services.subscription.service.SubscriptionService", config
    )


def register_identity_session(context, email: str, access_token: str) -> None:
    # Queue the session object as the next return values for identity-service RPC
    # calls (verify_session). The number of queued values can be controlled by a
    # scenario tag (e.g. @identity_sessions_2).
    from hashlib import sha256

    digest = sha256(email.encode("utf-8")).hexdigest()
    user_id = f"usr_{digest[:20]}"
    context.last_user_id = user_id
    repeats = getattr(context, "identity_session_repeats", 1)
    session = {"user_id": user_id, "email": email}
    for _ in range(repeats):
        context.manager.add_remote_return_value("identity-service", session)


__all__ = [
    "http_request",
    "register_identity_session",
    "start_subscription_subprocess",
]
