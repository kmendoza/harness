#!/bin/bash
curl --request PUT http://localhost:8500/v1/agent/check/pass/service:test-service-${1}
