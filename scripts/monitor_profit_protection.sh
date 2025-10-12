#!/bin/bash
# Monitor profit protection execution in real-time
# Run this to watch for automatic stop-loss and take-profit trades

echo "🔍 Monitoring Phase 9A Profit Protection..."
echo "=============================================="
echo ""
echo "⏰ fast_trading_evaluation runs every 10 minutes"
echo "📊 Next cycle expected around: $(date -v +5M '+%H:%M:%S')"
echo ""
echo "Watching for:"
echo "  🚨 PROFIT PROTECTION OVERRIDE - Profit protection triggers"
echo "  💰 Trade attempts - Actual trade executions"
echo "  ✅ Successful trades - Confirmed on Coinbase"
echo ""
echo "=============================================="
echo ""

# Monitor backend logs in real-time
tail -f /Users/lazy_genius/Projects/trader/logs/backend.log | \
  grep --line-buffered -E \
    "PROFIT PROTECTION OVERRIDE|Trade attempts|trade_attempts|Executing.*sell|SELL order placed|automatic_trade"
