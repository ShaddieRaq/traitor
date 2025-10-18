#!/bin/bash
# Quick lifecycle monitor - shows P/L exits and state transitions

echo "🔍 Watching for Lifecycle Events..."
echo "⏰ Next evaluation: ~12:12 PM (in 3 minutes)"
echo ""
echo "Expected within 10 minutes:"
echo "  ✅ 2 take profits (DASH +40%, ZORA +34%)"
echo "  🛑 11 stop losses (AVNT -42%, FLOKI -26%, etc.)"
echo "  🔄 13 bots: ACTIVE → CLOSING"
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "📺 LIVE LOG (Press Ctrl+C to stop)"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

tail -f logs/backend.log logs/celery-worker.log 2>/dev/null | grep --line-buffered -iE "(pnl protection|lifecycle|→ closing|→ closed|take_profit|stop_loss|archiv|resurrect)" | while read line; do
    case "$line" in
        *"P/L PROTECTION"*) echo "🎯 $line" ;;
        *"TAKE_PROFIT"*) echo "✅ $line" ;;
        *"STOP_LOSS"*) echo "🛑 $line" ;;
        *"→ CLOSING"*) echo "🔄 $line" ;;
        *"→ CLOSED"*) echo "⏸️  $line" ;;
        *"→ ARCHIVED"*) echo "📦 $line" ;;
        *"RESURRECTED"*) echo "♻️  $line" ;;
        *) echo "   $line" ;;
    esac
done
