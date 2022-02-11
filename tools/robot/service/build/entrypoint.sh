#!/bin/sh

if [ "$1" = 'robot' ]; then
    (cd /opt/robot && make robot)
else
    exec "$@"
fi

