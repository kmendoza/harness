#!/bin/sh

WEBHOOK_URL=${SLACK_WEBHOOK_URL:?SLACK_WEBHOOK_URL not set!}

DATA=$(cat)

echo -----
echo $DATA
echo -----

PAYLOAD=$(echo "$DATA" | jq -r '
  if type == "array" and length > 0 then
    "🚨 *Check:* \(.[]?.CheckID)\n*Status:* \(.[]?.Status)\n*Output:* \(.[]?.Output)"
  else
    "❌ Invalid alert data"
  end
')

# echo "Sending alert to Slack..." >&2
# curl -X POST -H "Content-Type: application/json" \
#      -d "{\"text\": \"$PAYLOAD\"}" \
#      "$WEBHOOK_URL"
