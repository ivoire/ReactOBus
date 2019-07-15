#!/bin/sh

[ -n "$1" ] && exec "$@"

exec python3 -m reactobus
