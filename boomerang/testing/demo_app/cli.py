"""CLI to flip demo-app-service degraded flag via RPC (for make targets)."""

import argparse
import asyncio
import sys

from kontiki.messaging import Messenger, RpcProxy

from boomerang.testing.demo_app.service import DEMO_APP_SERVICE_NAME

DEFAULT_AMQP_URL = "amqp://guest:guest@localhost/"


class DemoAppRpcProxy(RpcProxy):
    def __init__(self, messenger):
        super().__init__(messenger, service_name=DEMO_APP_SERVICE_NAME)


async def set_degraded(degraded):
    async with Messenger(
        amqp_url=DEFAULT_AMQP_URL,
        standalone=True,
        client_name="demo-app-cli",
    ) as messenger:
        return await DemoAppRpcProxy(messenger).set_degraded(degraded=degraded)


async def get_degraded():
    async with Messenger(
        amqp_url=DEFAULT_AMQP_URL,
        standalone=True,
        client_name="demo-app-cli",
    ) as messenger:
        return await DemoAppRpcProxy(messenger).get_degraded()


def main(argv=None):
    parser = argparse.ArgumentParser(
        description="Control demo-app-service degraded state over RPC."
    )
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("degrade", help="Mark demo-app-service as degraded")
    sub.add_parser("recover", help="Clear demo-app-service degraded flag")
    sub.add_parser("status", help="Print current degraded flag")

    args = parser.parse_args(argv)
    if args.command == "status":
        result = asyncio.run(get_degraded())
    elif args.command == "degrade":
        result = asyncio.run(set_degraded(True))
    else:
        result = asyncio.run(set_degraded(False))
    print(result)
    return 0


if __name__ == "__main__":
    sys.exit(main())
