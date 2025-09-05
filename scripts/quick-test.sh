#!/bin/bash

# Quick Testing Workflow (abbreviated version)
# For rapid validation during development

echo "⚡ QUICK TEST WORKFLOW"
echo "====================="

# Quick restart
./scripts/restart.sh

# Quick test run  
./scripts/test.sh --tb=short

# Quick sync check
curl -s -X POST "http://localhost:8000/api/v1/coinbase-sync/sync-coinbase-trades" | python3 -c "
import json, sys
data = json.load(sys.stdin)
if data.get('success'): 
    print(f'✅ Sync: {data.get(\"new_trades_synced\", 0)} new trades')
else: 
    print(f'❌ Sync failed: {data.get(\"error\", \"Unknown\")}')"

# Quick position check
./scripts/position-reconcile.sh check | tail -3

echo "✅ Quick workflow complete"
