#!/bin/sh

set -e

if [ "$1" = "setup" ]
then
  apt-get -q update
  apt-get install --no-install-recommends --yes black
else
  set -x
  LC_ALL=C.UTF-8 LANG=C.UTF-8 black --check .
fi
