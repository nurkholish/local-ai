#!/bin/bash
set -euo pipefail

KONG_URL="${KONG_URL:-http://localhost:8000}"
API_KEY="${API_KEY:-dev-key}"

echo "Waiting for Kong at $KONG_URL ..."
ok=0
for i in $(seq 1 30); do
  if curl -sf -o /dev/null -H "x-api-key: $API_KEY" "$KONG_URL/healthz"; then
    echo "  Kong up after $i attempts"
    ok=1
    break
  fi
  sleep 2
done

if [ "$ok" -ne 1 ]; then
  echo "ERROR: Kong not reachable"
  docker compose ps || true
  docker compose logs kong --tail=30 || true
  exit 1
fi

echo "Testing chat via Kong ..."
response=$(curl -sf -X POST "$KONG_URL/v1/chat" \
  -H "x-api-key: $API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"message":"What is 23*17? Use calculator."}')

echo "$response" | head -c 800
echo

if ! echo "$response" | grep -q '"answer"'; then
  echo "ERROR: response missing answer"
  exit 1
fi

echo "Smoke OK ✅"