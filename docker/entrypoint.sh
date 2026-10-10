#!/bin/sh
if [ "$1" = "sh" ] || [ "$1" = "/bin/sh" ]; then
  exec "$@"
fi
case "$1" in
  boomerang-*)
    exec "$@"
    ;;
esac
if [ -n "$SERVICE" ]; then
  exec "/usr/local/bin/boomerang-$SERVICE" "$@"
fi
exec "$@"
