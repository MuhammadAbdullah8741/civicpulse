#!/bin/sh
set -eu
BACKEND_UPSTREAM="${BACKEND_UPSTREAM:-backend:8000}"
if ! printf '%s' "$BACKEND_UPSTREAM" | grep -Eq '^[A-Za-z0-9][A-Za-z0-9.-]*:[0-9]{1,5}$'; then
    echo 'BACKEND_UPSTREAM must be a hostname:port value.' >&2
    exit 1
fi
DNS_RESOLVER="$(awk '/^nameserver/ {print $2; exit}' /etc/resolv.conf)"
if [ -z "$DNS_RESOLVER" ]; then
    echo 'No DNS resolver found in container configuration.' >&2
    exit 1
fi
export BACKEND_UPSTREAM DNS_RESOLVER
# Restrict substitution so nginx variables such as $uri are preserved.
envsubst '${BACKEND_UPSTREAM} ${DNS_RESOLVER}' \
    < /etc/nginx/civicpulse.conf.template > /tmp/civicpulse-nginx.conf
exec "$@"
