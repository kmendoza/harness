#! /bin/bash
echo "[re]registering file ${1}"
curl --request PUT --data @${1} http://localhost:8500/v1/agent/service/register
