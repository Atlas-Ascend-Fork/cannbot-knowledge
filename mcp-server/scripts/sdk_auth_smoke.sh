#!/usr/bin/env bash
# SDK auth 栈部署后冒烟自检：起本地实例 → 发现 → 设备码 → 令牌 → MCP。
# 用法: bash mcp-server/scripts/sdk_auth_smoke.sh [端口]   (默认 18901)
set -euo pipefail
PORT="${1:-18901}"
BASE="http://127.0.0.1:${PORT}"
DB="$(mktemp -d)/smoke.db"
cd "$(dirname "$0")/.."

echo "[1/5] 启动服务(SDK_AUTH=on, 端口 $PORT)"
CANNBOT_MCP_PORT="$PORT" CANNBOT_MCP_HOST=127.0.0.1 \
  CANNBOT_MCP_SDK_AUTH=on CANNBOT_MCP_PUBLIC_URL="$BASE" \
  CANNBOT_MCP_AUTH_DB="$DB" CANNBOT_MCP_AUTH_SECRET=smoke \
  CANNBOT_MCP_LOG=off .venv/bin/python server.py --transport http \
  > /tmp/sdk-smoke.log 2>&1 &
SRV=$!
trap 'kill $SRV 2>/dev/null || true' EXIT
sleep 3

echo "[2/5] 发现链"
curl -sf --max-time 5 "$BASE/.well-known/oauth-protected-resource" | grep -q '"resource"' || { echo "FAIL: 9728"; exit 1; }
curl -sf --max-time 5 "$BASE/.well-known/oauth-authorization-server" | grep -q '"issuer"' || { echo "FAIL: 8414"; exit 1; }

echo "[3/5] 设备码"
DC=$(curl -sf --max-time 5 -X POST "$BASE/oauth/device/code" -d "client_id=cannbot-knowledge-public")
DEVICE_CODE=$(echo "$DC" | python3 -c 'import json,sys;print(json.load(sys.stdin)["device_code"])')
USER_CODE=$(echo "$DC" | python3 -c 'import json,sys;print(json.load(sys.stdin)["user_code"])')
CK=$(mktemp)
curl -sf --max-time 5 -c "$CK" -X POST "$BASE/activate" --data-urlencode "user_code=$USER_CODE" -o /dev/null
curl -sf --max-time 5 -b "$CK" -X POST "$BASE/activate" --data-urlencode "user_code=$USER_CODE" --data-urlencode "username=smoke" --data-urlencode "action=allow" -o /dev/null

echo "[4/5] 换令牌"
AT=$(curl -sf --max-time 8 -X POST "$BASE/oauth/device/token" \
  --data-urlencode "grant_type=urn:ietf:params:oauth:grant-type:device_code" \
  --data-urlencode "device_code=$DEVICE_CODE" \
  --data-urlencode "client_id=cannbot-knowledge-public" \
  | python3 -c 'import json,sys;print(json.load(sys.stdin)["access_token"])')
[ -n "$AT" ] || { echo "FAIL: token"; exit 1; }

echo "[5/5] MCP initialize"
curl -sf --max-time 15 -X POST "$BASE/mcp" -H "Authorization: Bearer $AT" \
  -H 'Content-Type: application/json' -H 'Accept: application/json, text/event-stream' \
  -d '{"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2025-06-18","capabilities":{},"clientInfo":{"name":"smoke","version":"1"}}}' \
  | grep -q cannbot-knowledge || { echo "FAIL: initialize"; exit 1; }

echo "SMOKE OK — SDK auth 栈全链路正常"
