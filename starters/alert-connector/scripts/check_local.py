"""Verify local RabbitMQ is reachable for make check-local / run-local."""

import socket
import sys

HOST = "127.0.0.1"
PORT = 5672


def main():
    try:
        with socket.create_connection((HOST, PORT), timeout=2):
            pass
    except OSError as exc:
        print(
            "Local Boomerang broker is not reachable at %s:%s (%s).\n"
            "\n"
            "Start a compatible stack from the Boomerang monorepo, for example:\n"
            "  make stack-embedded-up\n"
            "  make stack-up\n"
            "  make run-dev-platform\n"
            "\n"
            "This starter only runs the connector; it does not start RabbitMQ."
            % (HOST, PORT, exc),
            file=sys.stderr,
        )
        return 1

    print("OK: AMQP broker reachable at %s:%s" % (HOST, PORT))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
