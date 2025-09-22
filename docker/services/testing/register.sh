#!/bin/bash
curl --request PUT http://localhost:8500/v1/agent/service/register \
--data "{
  \"Name\": \"test-service-${1}\",
  \"ID\": \"test-service-${1}\",
  \"Port\": 8080,
  \"Check\": {
    \"TTL\": \"10m\",
    \"DeregisterCriticalServiceAfter\": \"15m\"
  }
}"