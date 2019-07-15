#!/bin/sh

if [ "$1" = "reactobus" ]
then
  shift
  exec python3 -m reactobus "$@"
elif [ -n "$1" ]
then
  exec "$@"
else
  exec python3 -m reactobus
fi
