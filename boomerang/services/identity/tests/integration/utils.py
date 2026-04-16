from boomerang.testing import http_request, start_kontiki_subprocess


def start_identity_subprocess(config):
    return start_kontiki_subprocess(
        "boomerang.services.identity.service.IdentityService", config
    )


__all__ = ["http_request", "start_identity_subprocess"]
