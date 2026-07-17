"""Call pedagogical emit_demo_alert on the host-run connector (skeleton only)."""

import asyncio
import sys

from kontiki.messaging import Messenger

SERVICE_NAME = "alert-connector-demo-service"
AMQP_URL = "amqp://guest:guest@localhost/"


async def main():
    async with Messenger(standalone=True, amqp_url=AMQP_URL) as messenger:
        result = await messenger.call(SERVICE_NAME, "emit_demo_alert")
    print(result)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except Exception as exc:
        print(
            "emit_demo_alert failed: %s\n"
            "\n"
            "Prerequisites:\n"
            "  make stack-up\n"
            "  make run-local   # leave running in another terminal\n" % exc,
            file=sys.stderr,
        )
        raise SystemExit(1) from exc
