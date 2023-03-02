#!/bin/sh

if [ "$1" = 'help' ]; then
   echo ""
   echo "server  :  Listen on port PORT  for HTTP requests on subpath /alpine/public"
   echo "server  :  export PORT=8080"
   echo ""
elif [ "$1" = 'server' ]; then
   exec  /usr/sbin/lighttpd -D -f /etc/lighttpd/lighttpd.conf 
else
    exec "$@"
fi

