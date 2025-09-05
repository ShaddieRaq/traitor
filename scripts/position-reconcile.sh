#!/bin/bash

# Position Reconciliation Script
# Checks and optionally fixes position tracking discrepancies

echo "🔍 Position Reconciliation Tool"
echo "==============================="

# Function to check discrepancies
check_discrepancies() {
    echo "📊 Checking position discrepancies..."
    curl -s "http://localhost:8000/api/v1/position-reconciliation/discrepancies" | python3 -c "
import json, sys
data = json.load(sys.stdin)
discrepancies = data.get('discrepancies', [])
total = data.get('total_discrepancies', 0)

print(f'Found {total} position discrepancies:')
print()

if total == 0:
    print('✅ All bot positions are accurate!')
else:
    for disc in discrepancies:
        if 'error' not in disc:
            bot_name = disc['bot_name']
            tracked = disc['tracked_position_usd']
            actual = disc['actual_position_usd']
            diff = disc['difference_usd']
            pct_diff = disc['percentage_diff']
            print(f'❌ {bot_name}:')
            print(f'   Tracked: \${tracked:.2f}')
            print(f'   Actual:  \${actual:.2f}')
            print(f'   Diff:    \${diff:.2f} ({pct_diff:.1f}%)')
            print()
"
}

# Function to fix discrepancies
fix_discrepancies() {
    echo "🔧 Fixing position discrepancies..."
    curl -s -X POST "http://localhost:8000/api/v1/position-reconciliation/reconcile" | python3 -c "
import json, sys
data = json.load(sys.stdin)
results = data.get('results', {})
summary = results.get('summary', {})

print(f'Reconciliation Results:')
print(f'✅ Successful: {summary.get(\"successful_reconciliations\", 0)}')
print(f'❌ Failed: {summary.get(\"failed_reconciliations\", 0)}')
print(f'💰 Total adjustments: \${summary.get(\"total_adjustments_usd\", 0):.2f}')
print()

for bot in results.get('reconciled_bots', []):
    if bot.get('updated'):
        print(f'✅ {bot[\"bot_name\"]}: {bot[\"message\"]}')
    else:
        print(f'ℹ️  {bot[\"bot_name\"]}: {bot[\"message\"]}')
print()
print('✅ Position reconciliation complete!')
"
}

# Main menu
if [ "$1" = "check" ]; then
    check_discrepancies
elif [ "$1" = "fix" ]; then
    fix_discrepancies
elif [ "$1" = "both" ]; then
    check_discrepancies
    echo
    echo "Press Enter to proceed with fixes, or Ctrl+C to cancel..."
    read
    fix_discrepancies
else
    echo "Usage:"
    echo "  $0 check    - Check for position discrepancies"
    echo "  $0 fix      - Fix position discrepancies"
    echo "  $0 both     - Check then fix (with confirmation)"
    echo
    echo "Examples:"
    echo "  ./scripts/position-reconcile.sh check"
    echo "  ./scripts/position-reconcile.sh fix"
    echo "  ./scripts/position-reconcile.sh both"
fi
