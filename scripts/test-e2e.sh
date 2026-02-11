#!/bin/bash
set -e

API_URL="http://api.k8s.local" # Adjust if running outside cluster/ingress
STORE_NAME="test-store-$(date +%s)"

echo "🧪 Running E2E test..."

if ! curl -s "$API_URL/health" > /dev/null; then
  echo "❌ API is not reachable at $API_URL"
  exit 1
fi

# 1. Create store
echo "📦 Creating store: $STORE_NAME"
CREATE_RESPONSE=$(curl -s -X POST "$API_URL/api/v1/stores" \
  -H "Content-Type: application/json" \
  -d "{\"name\": \"$STORE_NAME\", \"engine\": \"woocommerce\"}")

STORE_ID=$(echo $CREATE_RESPONSE | jq -r '.id')
echo "✅ Store created: $STORE_ID"

# 2. Wait for ready status
echo "⏳ Waiting for store to be ready..."
for i in {1..60}; do
  STATUS=$(curl -s "$API_URL/api/v1/stores/$STORE_ID" | jq -r '.status')
  echo "   Status: $STATUS"
  
  if [ "$STATUS" == "ready" ]; then
    echo "✅ Store is ready!"
    break
  elif [ "$STATUS" == "failed" ]; then
    echo "❌ Store provisioning failed"
    exit 1
  fi
  
  sleep 10
done

# 3. Get URLs
STORE_DATA=$(curl -s "$API_URL/api/v1/stores/$STORE_ID")
STOREFRONT_URL=$(echo $STORE_DATA | jq -r '.storefront_url')
ADMIN_URL=$(echo $STORE_DATA | jq -r '.admin_url')

echo "🌐 Storefront: $STOREFRONT_URL"
echo "🔧 Admin: $ADMIN_URL"

# 4. Delete store
echo "🗑️  Deleting store..."
curl -s -X DELETE "$API_URL/api/v1/stores/$STORE_ID"

echo "✅ E2E test passed!"
