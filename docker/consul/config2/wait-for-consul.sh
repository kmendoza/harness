#!/bin/sh

CONSUL_ADDR=${CONSUL_HTTP_ADDR:-http://consul:8500}

echo "⏳ Waiting for Consul at $CONSUL_ADDR..."
until curl -s "$CONSUL_ADDR/v1/status/leader" | grep -q '\"'; do
  sleep 1
done
echo "✅ Consul is up!"
