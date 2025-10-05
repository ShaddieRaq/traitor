#!/bin/bash
# UI Learning System Verification Guide
# Run this to see what the UI should show

echo "🎯 LEARNING SYSTEM UI VERIFICATION GUIDE"
echo "========================================"
echo ""

echo "1. 📊 INTELLIGENCE FRAMEWORK PANEL"
echo "   Location: AI Intelligence tab"
echo "   Should show: '45/45 ACTIVE' learning status"
echo ""

echo "2. 🧠 LEARNING-ENHANCED BOT CARDS"
echo "   Location: Trading Overview tab"
echo "   Examples to look for:"
echo ""

# Show specific bot examples
echo "   🔥 SQD-USD (Major Loser - Aggressive Rebalance):"
curl -s "http://localhost:8000/api/v1/bots/" | jq '.[] | select(.pair == "SQD-USD") | {
  pair: .pair,
  rsi_weight: (.signal_config.rsi.weight * 100 | floor),
  ma_weight: (.signal_config.moving_average.weight * 100 | floor),
  strategy: "Aggressive Rebalance"
}'

echo ""
echo "   🌟 AVNT-USD (Major Winner - Fine Tune):"
curl -s "http://localhost:8000/api/v1/bots/" | jq '.[] | select(.pair == "AVNT-USD") | {
  pair: .pair,
  rsi_weight: (.signal_config.rsi.weight * 100 | floor),
  ma_weight: (.signal_config.moving_average.weight * 100 | floor),
  strategy: "Fine Tune"
}'

echo ""
echo "   📈 BTC-USD (Minor Loser - Moderate Rebalance):"
curl -s "http://localhost:8000/api/v1/bots/" | jq '.[] | select(.pair == "BTC-USD") | {
  pair: .pair,
  rsi_weight: (.signal_config.rsi.weight * 100 | floor),
  ma_weight: (.signal_config.moving_average.weight * 100 | floor),
  strategy: "Moderate Rebalance"
}'

echo ""
echo "3. 🎯 WHAT TO LOOK FOR IN BOT CARDS:"
echo "   ✅ Brain icon (🧠) next to pair name"
echo "   ✅ 'Learning Active' green badge"
echo "   ✅ Signal weight bars with modified percentages"
echo "   ✅ Strategy indicators (Aggressive/Moderate/Fine Tune)"
echo ""

echo "4. 📋 TOTAL LEARNING BOTS:"
learning_count=$(curl -s "http://localhost:8000/api/v1/bots/" | jq '[.[] | select(.signal_config.rsi.weight != 0.4 or .signal_config.moving_average.weight != 0.35 or .signal_config.macd.weight != 0.25)] | length')
echo "   Should show: ${learning_count}/45 learning-enhanced bots"
echo ""

echo "🌐 Open http://localhost:3000 and navigate through:"
echo "   1. Trading Overview tab → Look for brain icons on bot cards"
echo "   2. AI Intelligence tab → Check '45/45 ACTIVE' in Framework Panel"
echo "   3. AI Intelligence tab → Scroll to Learning Performance Dashboard"