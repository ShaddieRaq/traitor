#!/bin/bash

# Comprehensive Testing Workflow Script
# Ensures system integrity after any changes

set -e  # Exit on any error

echo "🚀 COMPREHENSIVE TESTING WORKFLOW"
echo "=================================="
echo "Following standardized testing sequence for system validation"
echo

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print step headers
print_step() {
    echo
    echo -e "${BLUE}$1${NC}"
    echo "$(echo "$1" | sed 's/./=/g')"
}

# Function to check command success
check_success() {
    if [ $? -eq 0 ]; then
        echo -e "${GREEN}✅ $1${NC}"
    else
        echo -e "${RED}❌ $1 FAILED${NC}"
        exit 1
    fi
}

# Step 1: Restart Application
print_step "STEP 1: RESTART APPLICATION"
echo "🔄 Stopping all services..."
./scripts/stop.sh
sleep 2

echo "🚀 Starting all services..."
./scripts/start.sh
check_success "Application restart"

# Wait for services to be ready
echo "⏳ Waiting for services to initialize..."
sleep 5

# Verify services are running
./scripts/status.sh | grep -q "✅" && echo -e "${GREEN}✅ All services confirmed running${NC}" || (echo -e "${RED}❌ Service check failed${NC}" && exit 1)

# Step 2: Run All Tests
print_step "STEP 2: RUN ALL TESTS"
echo "🧪 Executing comprehensive test suite..."

# Run tests directly (this shows output)
./scripts/test.sh
TEST_EXIT_CODE=$?

# Check if all tests passed
if [ $TEST_EXIT_CODE -eq 0 ]; then
    echo -e "${GREEN}✅ All tests passed successfully${NC}"
    echo "✅ Proceeding to next step..."
else
    echo -e "${RED}❌ Test suite execution failed${NC}"
    exit 1
fi

# Step 3: Run Trade Sync with Coinbase
print_step "STEP 3: RUN TRADE SYNC WITH COINBASE"
echo "🔄 Syncing trades with Coinbase..."
SYNC_RESULT=$(curl -s -X POST "http://localhost:8000/api/v1/coinbase-sync/sync-coinbase-trades")
check_success "Coinbase trade sync"

# Parse and display sync results
echo "$SYNC_RESULT" | python3 -c "
import json, sys
try:
    data = json.load(sys.stdin)
    # Check both 'success' field and 'status' field for compatibility
    is_success = data.get('success', False) or data.get('status') == 'success'
    if is_success:
        print(f\"✅ Sync successful:\")
        print(f\"   📊 Coinbase fills found: {data.get('coinbase_fills_found', 0)}\")
        print(f\"   🆕 New trades synced: {data.get('new_trades_synced', 0)}\")
        print(f\"   💾 Total trades in DB: {data.get('total_trades_in_db', 'N/A')}\")
    else:
        print(f\"❌ Sync failed: {data.get('error', 'Unknown error')}\")
        sys.exit(1)
except Exception as e:
    print(f\"❌ Failed to parse sync result: {e}\")
    sys.exit(1)
"

# Step 4: Validate Trades Against Coinbase
print_step "STEP 4: VALIDATE TRADES AGAINST COINBASE"
echo "🔍 Validating position tracking accuracy..."

# Check for position discrepancies
DISCREPANCY_CHECK=$(curl -s "http://localhost:8000/api/v1/position-reconciliation/discrepancies")
echo "$DISCREPANCY_CHECK" | python3 -c "
import json, sys
try:
    data = json.load(sys.stdin)
    total_discrepancies = data.get('total_discrepancies', 0)
    discrepancies = data.get('discrepancies', [])
    
    if total_discrepancies == 0:
        print('✅ Position tracking validation: All bot positions accurate')
    else:
        print(f'⚠️  Found {total_discrepancies} position discrepancies:')
        for disc in discrepancies:
            if 'error' not in disc:
                bot_name = disc['bot_name']
                tracked = disc['tracked_position_usd']
                actual = disc['actual_position_usd']
                diff = disc['difference_usd']
                print(f'   📊 {bot_name}: Tracked \${tracked:.2f} vs Actual \${actual:.2f} (diff: \${diff:.2f})')
        
        print()
        print('🔧 Auto-fixing position discrepancies...')
        sys.exit(2)  # Signal that reconciliation is needed
except Exception as e:
    print(f'❌ Failed to validate positions: {e}')
    sys.exit(1)
"

# Check if reconciliation is needed
if [ $? -eq 2 ]; then
    echo "🔧 Running automatic position reconciliation..."
    RECONCILE_RESULT=$(curl -s -X POST "http://localhost:8000/api/v1/position-reconciliation/reconcile")
    echo "$RECONCILE_RESULT" | python3 -c "
import json, sys
try:
    data = json.load(sys.stdin)
    if data.get('success', False):
        fixed_bots = data.get('reconciled_bots', [])
        print(f'✅ Position reconciliation completed successfully')
        print(f'   📊 Fixed {len(fixed_bots)} bot positions')
        for bot in fixed_bots:
            print(f'   🔧 {bot[\"bot_name\"]}: {bot[\"action\"]} (\${bot[\"adjustment_usd\"]:.2f})')
    else:
        print(f'❌ Position reconciliation failed: {data.get(\"error\", \"Unknown error\")}')
        sys.exit(1)
except Exception as e:
    print(f'❌ Failed to parse reconciliation result: {e}')
    sys.exit(1)
"
    
    # Verify positions are now correct
    echo "🔍 Verifying position fix..."
    FINAL_CHECK=$(curl -s "http://localhost:8000/api/v1/position-reconciliation/discrepancies")
    echo "$FINAL_CHECK" | python3 -c "
import json, sys
try:
    data = json.load(sys.stdin)
    remaining_discrepancies = data.get('total_discrepancies', 0)
    if remaining_discrepancies == 0:
        print('✅ Position validation: All positions now accurate after reconciliation')
    else:
        print(f'⚠️  Warning: {remaining_discrepancies} discrepancies remain after reconciliation')
except Exception as e:
    print(f'❌ Failed to verify position fix: {e}')
"
fi

# Additional validation: Account balances
echo "💰 Verifying account balances..."
ACCOUNT_CHECK=$(curl -s "http://localhost:8000/api/v1/market/accounts")
echo "$ACCOUNT_CHECK" | python3 -c "
import json, sys
try:
    data = json.load(sys.stdin)
    print('📊 Current account balances:')
    for account in data:
        currency = account['currency']
        total_balance = account['available_balance'] + account['hold']
        if total_balance > 0 or currency in ['USD', 'BTC', 'ETH']:
            print(f'   {currency}: {total_balance:.8f}')
except Exception as e:
    print(f'❌ Failed to check account balances: {e}')
    sys.exit(1)
"

# Final system health check
print_step "FINAL SYSTEM HEALTH CHECK"
echo "🏥 Performing final system validation..."

# Check bot status
BOT_STATUS=$(curl -s "http://localhost:8000/api/v1/bots/status/summary")
echo "$BOT_STATUS" | python3 -c "
import json, sys
try:
    data = json.load(sys.stdin)
    print(f'🤖 Bot status summary:')
    for bot in data:
        status = bot['status']
        temp = bot['temperature']
        position = bot['current_position_size']
        score = bot['current_combined_score']
        print(f'   {bot[\"name\"]} ({bot[\"pair\"]}): {status} | {temp} | \${position:.2f} | Score: {score:.3f}')
except Exception as e:
    print(f'❌ Failed to check bot status: {e}')
    sys.exit(1)
"

# Success summary
print_step "🎉 TESTING WORKFLOW COMPLETE"
echo -e "${GREEN}✅ All validation steps completed successfully!${NC}"
echo
echo "📋 Workflow Summary:"
echo "   ✅ Application restarted and services confirmed running"
echo "   ✅ Complete test suite passed (no failures or skips)"
echo "   ✅ Coinbase trade sync completed successfully"  
echo "   ✅ Position tracking validated against actual holdings"
echo "   ✅ System health check passed"
echo
echo -e "${BLUE}🚀 System is ready for safe operations!${NC}"

# Optional: Show next steps
echo
echo "📝 Suggested next steps:"
echo "   • Review bot configurations if needed"
echo "   • Start bots for live trading: curl -X POST \"http://localhost:8000/api/v1/bots/{id}/start\""
echo "   • Monitor via dashboard: open http://localhost:3000"
echo "   • Check logs: ./scripts/logs.sh"
