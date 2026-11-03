from boomerang.testing import http_request, start_kontiki_subprocess


def start_zulip_notifier_subprocess(config):
    return start_kontiki_subprocess(
        "boomerang.services.notifiers.zulip.service.ZulipNotifierService",
        config,
    )


__all__ = ["http_request", "start_zulip_notifier_subprocess"]
