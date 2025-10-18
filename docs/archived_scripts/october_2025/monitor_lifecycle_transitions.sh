#!/bin/bash
# Monitor Bot Lifecycle Transitions in Real-Time
#
# This script shows:
# - P/L protection triggers
# - Lifecycle state changes (ACTIVE → CLOSING → CLOSED)
# - Position liquidations
# - Capital reallocation

echo "🔍 Monitoring Bot Lifecycle System..."
echo "📋 Watching for:"
echo "   • P/L protection triggers (take profit / stop loss)"
echo "   • Lifecycle transitions (ACTIVE → CLOSING → CLOSED → ARCHIVED)"
echo "   • Position liquidations"
echo "   • Capital reallocation"
echo ""
echo "⏰ Next fast_trading_evaluation: ~every 10 minutes"
echo "⏰ Next check_closing_bots: ~every hour"
echo "⏰ Next daily_cleanup: Tomorrow 2 AM UTC"
echo ""
echo "📊 Current Bot Status:"
curl -s "http://localhost:8000/api/v1/bots/" | jq '
  group_by(.lifecycle_stage) | 
  map({
    stage: (.[0].lifecycle_stage // "NULL"),
    count: length,
    bots: [.[] | .pair]
  })
' 2>/dev/null || echo "   ⚠️  Could not fetch current status"

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "🎬 LIVE LOG STREAM (Press Ctrl+C to stop)"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

# Tail both backend and celery worker logs
tail -f logs/backend.log logs/celery-worker.log 2>/dev/null | grep --line-buffered -E "(P/L PROTECTION|lifecycle|CLOSING|CLOSED|ARCHIVED|transition|liquidat|capital reallocation|Breakout scanner|resurrection)" | while read -r line; do
    # Color code different event types
    if [[ $line == *"P/L PROTECTION"* ]]; then
        echo "🎯 $line"
    elif [[ $line == *"TAKE_PROFIT"* ]]; then
        echo "✅ $line"
    elif [[ $line == *"STOP_LOSS"* ]]; then
        echo "🛑 $line"
    elif [[ $line == *"→ CLOSING"* ]]; then
        echo "🔄 $line"
    elif [[ $line == *"→ CLOSED"* ]]; then
        echo "⏸️  $line"
    elif [[ $line == *"→ ARCHIVED"* ]]; then
        echo "📦 $line"
    elif [[ $line == *"RESURRECTED"* ]]; then
        echo "♻️  $line"
    elif [[ $line == *"capital reallocation"* ]]; then
        echo "💰 $line"
    else
        echo "   $line"
    fi
done
