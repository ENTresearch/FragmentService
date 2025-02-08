#!/bin/bash

set -e

if [ -z "$API_DOMAIN" ]
then
    export API_DOMAIN="localhost"
fi

caddy run --config /etc/caddy/Caddyfile --adapter caddyfile