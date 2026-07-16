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
            "Local AMQP broker is not reachable at %s:%s (%s).\n"
            "\n"
            "From this starter directory, start the demo stack:\n"
            "  make stack-up\n"
            "\n"
            "Then run the connector with: make run-local\n"
            "(Host ports 5672 / 1025 / 8025 / 15672 must be free.)"
            % (HOST, PORT, exc),
            file=sys.stderr,
        )
        return 1

    print("OK: AMQP broker reachable at %s:%s" % (HOST, PORT))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
