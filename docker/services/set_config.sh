#!/bin/bash

SERVICE_ID='harness-test'
CONSUL_URL="http://localhost:8500"
BASE_PATH="services/prod/${SERVICE_ID}"

# harness data
curl -X PUT "${CONSUL_URL}/v1/kv/${BASE_PATH}/harness" \
  -d '{"interface": "0.0.0.0", "port": 3000}'

# app-data
curl -X PUT "${CONSUL_URL}/v1/kv/${BASE_PATH}/target-config" \
  -d '{"ch_host": "120.10.10.12", "ch_port": "8123, "ch_user": "gary", "ch_pass": "secret"}'

# logging config
curl -X PUT "${CONSUL_URL}/v1/kv/${BASE_PATH}/logging" \
  -d @logging-conf.json

echo "All keys set successfully!"