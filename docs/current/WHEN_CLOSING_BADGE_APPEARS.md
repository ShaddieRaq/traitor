# When Does a Bot Get the ⏳ CLOSING Badge?

**Date**: October 12, 2025  
**Question**: "When does it get the closing badge?"

## 🎯 Quick Answer

A bot gets the **⏳ CLOSING** badge when it has an **open position** and hits ANY of these three exit triggers:

1. **🎯 Take Profit**: Position reaches **+10% gain**
2. **🛑 Stop Loss**: Position reaches **-5% loss**
3. **⏰ Time Limit**: BREAKOUT bot holds position for **72+ hours** (3 days)

---

## 📊 Detailed Trigger Conditions

### 1. 🎯 Take Profit Exit
**Trigger**: Position P/L ≥ +10%

```python
# From bot_evaluator.py
take_profit_pct = bot.take_profit_pct  # Default: 10.0%
if pnl_pct >= take_profit_pct:
    # CLOSING badge appears!
    lifecycle_service.transition_to_closing(bot, reason='TAKE_PROFIT')
```

**Example**:
- Bot buys BTC-USD at $40,000
- BTC price rises to $44,000
- P/L = +10%
- ✅ ACTIVE → ⏳ CLOSING
- Market sell order placed to lock gains

---

### 2. 🛑 Stop Loss Exit
**Trigger**: Position P/L ≤ -5%

```python
# From bot_evaluator.py
stop_loss_pct = bot.stop_loss_pct  # Default: 5.0%
if pnl_pct <= -stop_loss_pct:
    # CLOSING badge appears!
    lifecycle_service.transition_to_closing(bot, reason='STOP_LOSS')
```

**Example**:
- Bot buys ETH-USD at $2,000
- ETH price drops to $1,900
- P/L = -5%
- ✅ ACTIVE → ⏳ CLOSING
- Market sell order placed to cut loss

---

### 3. ⏰ Time Limit Exit (BREAKOUT Bots Only)
**Trigger**: Position held for ≥ 72 hours (3 days)

```python
# From bot_evaluator.py
if bot.trading_mode == 'BREAKOUT':
    holding_hours = time_since_last_buy
    max_holding_hours = 72  # 3 days
    
    if holding_hours >= max_holding_hours:
        # CLOSING badge appears!
        lifecycle_service.transition_to_closing(bot, reason='TIME_LIMIT')
```

**Example**:
- BREAKOUT bot buys AVAX-USD on momentum signal
- 72 hours pass (3 days)
- Current P/L = +3% (didn't hit take profit yet)
- ✅ ACTIVE → ⏳ CLOSING
- Market sell order placed to free capital

**Note**: Only applies to `trading_mode = 'BREAKOUT'` bots. Regular CORE bots don't have time limits.

---

## 🔄 Complete Badge Transition Flow

### Scenario 1: Take Profit Exit (Most Common Winner)

```
1. Bot has open position
   Badge: ✅ ACTIVE
   
2. Price moves up +10%
   Celery evaluation task detects: pnl_pct >= 10.0%
   
3. IMMEDIATELY triggers transition
   Badge: ✅ ACTIVE → ⏳ CLOSING
   Action: Market sell order placed
   
4. Order fills (usually <1 minute)
   Badge: ⏳ CLOSING → 🔒 CLOSED (48h)
   Status: bot.status = "STOPPED"
   
5. 48 hours pass
   Badge: 🔒 CLOSED → ✅ ACTIVE (resurrected)
           OR
           🔒 CLOSED → 📦 ARCHIVED (retired)
```

---

### Scenario 2: Stop Loss Exit (Loss Prevention)

```
1. Bot has open position
   Badge: ✅ ACTIVE
   
2. Price moves down -5%
   Celery evaluation task detects: pnl_pct <= -5.0%
   
3. IMMEDIATELY triggers transition
   Badge: ✅ ACTIVE → ⏳ CLOSING
   Action: Market sell order placed
   Warning: "🛑 STOP LOSS triggered"
   
4. Order fills (usually <1 minute)
   Badge: ⏳ CLOSING → 🔒 CLOSED (48h)
   Loss locked at -5% (prevents further damage)
   
5. 48 hours pass
   Badge: 🔒 CLOSED → 📦 ARCHIVED (likely retired)
   Capital freed and reallocated
```

---

### Scenario 3: Time Limit Exit (BREAKOUT Only)

```
1. BREAKOUT bot buys on momentum
   Badge: ✅ ACTIVE
   trading_mode: "BREAKOUT"
   
2. 72 hours pass (3 days)
   Celery evaluation detects: holding_hours >= 72
   Current P/L: +3% (didn't hit take profit)
   
3. Time limit triggers exit
   Badge: ✅ ACTIVE → ⏳ CLOSING
   Action: Market sell order placed
   Reason: "Short-term momentum play expired"
   
4. Order fills
   Badge: ⏳ CLOSING → 🔒 CLOSED (48h)
   +3% gain locked, capital freed
   
5. 48 hours pass
   Badge: 🔒 CLOSED → 📦 ARCHIVED
   Capital reallocated to new breakout opportunity
```

---

## ⏱️ Evaluation Timing

**How often are bots checked?**

Celery task `evaluate_bot_signals` runs every **few minutes** (exact interval configured in Celery beat):

```python
@celery_app.task
def evaluate_bot_signals():
    # Get all RUNNING bots
    active_bots = db.query(Bot).filter(Bot.status == "RUNNING").all()
    
    for bot in active_bots:
        # Evaluate signals and check P/L protection
        evaluation_result = evaluator.evaluate_bot(bot, market_data)
        
        # Check if P/L exit triggered
        if evaluation_result.get('pnl_protection'):
            pnl_exit = evaluation_result['pnl_protection']
            
            # Execute sell and transition to CLOSING
            if pnl_exit['reason'] in ['TAKE_PROFIT', 'STOP_LOSS', 'TIME_LIMIT']:
                # Badge changes to CLOSING here!
                lifecycle_service.transition_to_closing(bot, reason=pnl_exit['reason'])
```

**Typical lag**: 1-5 minutes between hitting threshold and badge change (depends on evaluation cycle timing).

---

## 🔍 Current Bot Status Check

Check if any bots have positions that might trigger soon:

```bash
# Check all bot positions and P/L
curl -s "http://localhost:8000/api/v1/bots/" | jq '[.[] | select(.current_position_size > 0) | {
  pair: .pair,
  lifecycle_stage: .lifecycle_stage,
  position_size: .current_position_size,
  entry_price: .current_position_entry_price
}]'
```

**Expected output** (if any bots have positions):
```json
[
  {
    "pair": "BTC-USD",
    "lifecycle_stage": "ACTIVE",
    "position_size": 0.0005,
    "entry_price": 40000.0
  }
]
```

To see actual P/L percentages, you'd need to fetch current prices and calculate manually.

---

## 📋 Badge Change Detection

### In Logs
Watch for these messages when badge changes:

```bash
tail -f logs/backend.log | grep "CLOSING\|TAKE_PROFIT\|STOP_LOSS"
```

**Example log entries**:
```
🎯 TAKE PROFIT triggered for BTC-USD: P/L 10.23% >= target 10.00%
🔄 Bot 1 (BTC-USD) → CLOSING | Reason: TAKE_PROFIT
✅ Automatic sell trade executed successfully for bot 1
✅ Bot 1 (BTC-USD) → CLOSED | Position liquidated
```

### In UI
- Badge instantly changes from **✅ ACTIVE** to **⏳ CLOSING**
- Usually within 1-5 minutes of hitting threshold
- Then quickly changes to **🔒 CLOSED (48h)** after order fills

---

## 🎯 Why You Haven't Seen It Yet

Your bots all show **✅ ACTIVE** because:

1. **System just implemented** (October 12, 2025)
2. **No positions hit ±5% yet** (or they did before lifecycle system existed)
3. **No BREAKOUT bots hit 72h limit** (or don't have BREAKOUT bots)

You'll see your first **⏳ CLOSING** badge when:
- First bot's position reaches +10% gain, OR
- First bot's position drops to -5% loss, OR
- First BREAKOUT bot holds position for 3 days

---

## 🧪 Testing (If You Want to Force It)

**To trigger CLOSING badge manually** (for testing):

1. **Lower thresholds temporarily**:
```bash
# Update bot with very tight thresholds
curl -X PUT "http://localhost:8000/api/v1/bots/1" \
  -H "Content-Type: application/json" \
  -d '{
    "take_profit_pct": 0.5,  // 0.5% instead of 10%
    "stop_loss_pct": 0.5     // 0.5% instead of 5%
  }'
```

2. **Wait for next price movement**
   - Bot will hit threshold much faster
   - Badge will change to CLOSING
   - Test the full lifecycle flow

3. **Restore normal thresholds after testing**
```bash
curl -X PUT "http://localhost:8000/api/v1/bots/1" \
  -H "Content-Type: application/json" \
  -d '{
    "take_profit_pct": 10.0,
    "stop_loss_pct": 5.0
  }'
```

---

## Summary

**⏳ CLOSING Badge Appears When**:
- 🎯 Position reaches **+10% profit** (take profit)
- 🛑 Position reaches **-5% loss** (stop loss)
- ⏰ BREAKOUT bot holds **72+ hours** (time limit)

**How Fast**:
- Detection: 1-5 minutes (evaluation cycle)
- Liquidation: <1 minute (market order fills)
- Total time in CLOSING: Usually 1-6 minutes

**Current State**:
- All your bots: ✅ ACTIVE
- Waiting for first P/L exit trigger
- Will happen naturally as positions move

**Next Badge**: You'll see **⏳ CLOSING** when your first bot hits any of the three exit triggers! 🚀
