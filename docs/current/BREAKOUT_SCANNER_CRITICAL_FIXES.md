# 🚨 Breakout Scanner - Critical Fixes Required

**Date**: October 12, 2025  
**Status**: ⚠️ **DO NOT ENABLE AUTO-TRADING** until these fixes are applied  
**Priority**: 🔥🔥🔥 **URGENT** - Addresses rate limiting + profit protection gaps

---

## 📋 **Issues Identified**

### 1. ❌ **NO PROFIT-TAKING LOGIC** (Critical - Caused Oct 10 Loss)
**Problem**: `bot_evaluator.py` completely ignores `take_profit_pct` and `stop_loss_pct` fields
```python
# Bot model HAS the fields:
bot.stop_loss_pct = 8.0
bot.take_profit_pct = 30.0
bot.current_position_entry_price = 0.7606

# But bot_evaluator.py ONLY checks signals:
if overall_score >= 0.05:  # Signal reversal
    return 'sell'

# ❌ NEVER CHECKS P&L-based exits!
```

**Impact**: Market crash on Oct 10 wiped out all unrealized gains because bots never locked profits

**Solution Required**: Add P&L exit logic BEFORE signal checking

---

### 2. ❌ **NO MULTI-TIMEFRAME ANALYSIS** (Can't Tell Early vs Late)
**Problem**: Only analyzes 24h snapshot, can't detect if we're catching breakout early or late
```python
# What we see:
price_change_24h = +44%  # Could be hour 1 or hour 23!

# What we CAN'T tell:
- When did the move start?
- Is momentum accelerating (early) or decelerating (late)?
- Are we catching it at the beginning or the top?
```

**Impact**: Might create bots for breakouts that are already exhausted

**Solution Required**: Add 1h, 4h, 24h timeframe analysis

---

### 3. 🔥 **HITTING COINBASE API DIRECTLY** (Causing Rate Limits)
**Problem**: `breakout_detector.py` bypasses existing infrastructure
```python
# Current (BAD):
def _fetch_all_products(self):
    products = self.coinbase_service.get_products()  # ✅ Good
    
    # But as fallback:
    response = requests.get('https://api.coinbase.com/...')  # ❌ BAD! Direct API call
```

**Impact**: Rate limiting issues (user reported still getting rate limits)

**Solution Required**: Route through MarketDataService with Redis caching

---

### 4. ⚠️ **WEBSOCKET STREAMING STATUS UNKNOWN**
**Problem**: Can't verify if WebSocket price streaming is active
```bash
curl "http://localhost:8000/api/v1/websocket-prices/status"
# Returns: 404 Not Found
```

**Impact**: If WebSocket isn't running, ALL bots hit REST API causing rate limits

**Solution Required**: Verify WebSocket is running, restart if needed

---

## 🔧 **Fix Implementation Plan**

### **FIX 1: Add P&L-Based Exit Logic** (HIGHEST PRIORITY)

**File**: `/backend/app/services/bot_evaluator.py`

**Add new method**:
```python
def should_sell_with_profit_protection(
    self, 
    bot: Bot, 
    current_price: float,
    overall_score: float
) -> tuple[bool, str]:
    """
    Check if bot should sell based on P&L or signals.
    
    Priority Order (highest to lowest):
    1. TAKE PROFIT - Lock gains at target
    2. STOP LOSS - Cut losses at limit
    3. TIME LIMIT - Exit stale positions (BREAKOUT bots only)
    4. SIGNAL REVERSAL - Existing logic
    
    Returns:
        (should_sell: bool, reason: str)
    """
    
    # Calculate current P&L if we have a position
    if bot.current_position_size and bot.current_position_entry_price:
        pnl_pct = ((current_price - bot.current_position_entry_price) 
                   / bot.current_position_entry_price * 100)
        
        # Priority 1: TAKE PROFIT
        if pnl_pct >= bot.take_profit_pct:
            logger.info(f"💰 {bot.pair}: Take profit triggered at +{pnl_pct:.2f}% (target: +{bot.take_profit_pct}%)")
            return True, f"TAKE_PROFIT:+{pnl_pct:.2f}%"
        
        # Priority 2: STOP LOSS
        if pnl_pct <= -bot.stop_loss_pct:
            logger.warning(f"🛑 {bot.pair}: Stop loss triggered at {pnl_pct:.2f}% (limit: -{bot.stop_loss_pct}%)")
            return True, f"STOP_LOSS:{pnl_pct:.2f}%"
    
    # Priority 3: TIME LIMIT (BREAKOUT bots only)
    if bot.trading_mode == "BREAKOUT" and bot.current_position_size > 0:
        age_hours = (datetime.utcnow() - bot.created_at).total_seconds() / 3600
        if age_hours >= 72:
            logger.info(f"⏰ {bot.pair}: Time limit exit at {age_hours:.1f}h (max: 72h)")
            return True, f"TIME_LIMIT:{age_hours:.1f}h"
    
    # Priority 4: SIGNAL REVERSAL (existing logic)
    if overall_score >= 0.05:
        return True, f"SIGNAL_SELL:{overall_score:.3f}"
    
    return False, "HOLD"
```

**Modify existing evaluate() method**:
```python
# Replace current sell logic:
if overall_score >= sell_threshold:
    return 'sell'

# With new P&L-aware logic:
should_sell, reason = self.should_sell_with_profit_protection(
    bot, current_price, overall_score
)
if should_sell:
    return 'sell'  # reason is logged inside method
```

**Testing**:
```bash
# Test with existing breakout bots
sqlite3 trader.db "SELECT id, pair, stop_loss_pct, take_profit_pct FROM bots WHERE trading_mode='BREAKOUT';"
# Expected: 54|TRAC-USDC|8.0|30.0, 55|ASM-USDC|5.0|15.0

# Manual test: Set current_position_entry_price and trigger evaluation
# Should see take-profit/stop-loss logging
```

---

### **FIX 2: Add Multi-Timeframe Analysis**

**File**: `/backend/app/services/breakout_detector.py`

**Add new method**:
```python
def _analyze_timeframes(self, product_id: str) -> dict:
    """
    Analyze multiple timeframes to detect breakout stage.
    
    Returns:
        {
            'change_1h': float,
            'change_4h': float,
            'change_24h': float,
            'stage': 'EARLY' | 'MID' | 'LATE' | 'STALE',
            'momentum': 'ACCELERATING' | 'STEADY' | 'DECELERATING'
        }
    """
    
    try:
        # Get historical candles (need to add this to coinbase_service)
        candles_1h = self.coinbase_service.get_candles(product_id, granularity='ONE_HOUR', limit=24)
        
        if not candles_1h or len(candles_1h) < 24:
            return {'stage': 'UNKNOWN', 'momentum': 'UNKNOWN'}
        
        # Calculate price changes across timeframes
        current_price = float(candles_1h[0]['close'])
        price_1h_ago = float(candles_1h[1]['close'])
        price_4h_ago = float(candles_1h[4]['close']) if len(candles_1h) > 4 else price_1h_ago
        price_24h_ago = float(candles_1h[23]['close']) if len(candles_1h) > 23 else price_4h_ago
        
        change_1h = ((current_price - price_1h_ago) / price_1h_ago * 100)
        change_4h = ((current_price - price_4h_ago) / price_4h_ago * 100)
        change_24h = ((current_price - price_24h_ago) / price_24h_ago * 100)
        
        # Determine momentum
        if change_1h > change_4h > change_24h:
            momentum = "ACCELERATING"  # Getting faster (GOOD)
        elif change_1h < change_4h < change_24h:
            momentum = "DECELERATING"  # Slowing down (BAD)
        else:
            momentum = "STEADY"
        
        # Estimate breakout stage
        # Find when price started moving up significantly
        breakout_start_idx = None
        for i in range(len(candles_1h) - 1, 0, -1):
            price_change_from_current = ((current_price - float(candles_1h[i]['close'])) 
                                         / float(candles_1h[i]['close']) * 100)
            if price_change_from_current < 5:  # Less than 5% move
                breakout_start_idx = i
                break
        
        if breakout_start_idx:
            age_hours = breakout_start_idx
            if age_hours < 6:
                stage = "EARLY"   # Fresh breakout
            elif age_hours < 12:
                stage = "MID"     # Mid-stage
            elif age_hours < 18:
                stage = "LATE"    # Late stage
            else:
                stage = "STALE"   # Probably topping
        else:
            stage = "UNKNOWN"
        
        return {
            'change_1h': change_1h,
            'change_4h': change_4h,
            'change_24h': change_24h,
            'stage': stage,
            'momentum': momentum,
            'age_hours': breakout_start_idx if breakout_start_idx else 0
        }
        
    except Exception as e:
        logger.error(f"Error analyzing timeframes for {product_id}: {e}")
        return {'stage': 'UNKNOWN', 'momentum': 'UNKNOWN'}
```

**Modify scoring**:
```python
def _calculate_breakout_score(...):
    # ... existing scoring ...
    
    # Add timeframe bonus/penalty
    timeframe_data = self._analyze_timeframes(product_id)
    
    # Bonus for early-stage accelerating breakouts
    if timeframe_data['stage'] == 'EARLY' and timeframe_data['momentum'] == 'ACCELERATING':
        score += 15  # Big bonus
        signals.append("EARLY_BREAKOUT:ACCELERATING")
    elif timeframe_data['stage'] == 'LATE' or timeframe_data['momentum'] == 'DECELERATING':
        score -= 20  # Penalty for stale/decelerating
        signals.append("LATE_STAGE:AVOID")
    
    return score, signals
```

---

### **FIX 3: Route Through MarketDataService** (Prevent Rate Limiting)

**File**: `/backend/app/services/breakout_detector.py`

**Current (BAD)**:
```python
def _fetch_all_products(self):
    products = self.coinbase_service.get_products()  # Goes to REST API
    
    # Fallback hits API directly!
    response = requests.get('https://api.coinbase.com/...')
```

**Fixed (GOOD)**:
```python
def __init__(self):
    # Add MarketDataService
    from app.services.market_data_service import get_market_data_service
    self.market_data_service = get_market_data_service()
    
def _fetch_all_products(self) -> List[Dict]:
    """Fetch all products via MarketDataService (cached)."""
    try:
        # Use MarketDataService which has Redis caching
        products = self.market_data_service.get_all_products()
        
        if products:
            logger.info(f"✅ Retrieved {len(products)} products from MarketDataService")
            # Convert ProductInfo objects to dicts
            return [p.to_dict() for p in products]
        
        logger.warning("MarketDataService returned no products")
        return []
        
    except Exception as e:
        logger.error(f"Error fetching products from MarketDataService: {e}")
        return []

def _get_product_24h_stats(self, product_id: str) -> dict:
    """Get 24h stats via MarketDataService (cached)."""
    try:
        # Use cached market data instead of direct API
        stats = self.market_data_service.get_product_stats(product_id)
        return stats
    except Exception as e:
        logger.error(f"Error getting stats for {product_id}: {e}")
        return {}
```

**Benefits**:
- ✅ Uses Redis cache (60s TTL) - 95%+ hit rate
- ✅ No direct Coinbase API calls
- ✅ Integrates with existing infrastructure
- ✅ Prevents rate limiting

---

### **FIX 4: Verify WebSocket Streaming**

**Check status**:
```bash
# Check if WebSocket price streaming is running
grep "💰.*USD:" logs/backend.log | tail -5

# Should see recent price updates like:
# 💰 BTC-USD: $65432.10
# 💰 ETH-USD: $3421.50
```

**If not running**:
```bash
# Start backend and check WebSocket
./scripts/start.sh

# Manually start WebSocket if needed
curl -X POST "http://localhost:8000/api/v1/websocket/start-price-streaming" | jq
```

**Add to breakout scanner**:
```python
def scan_all_products(self):
    """Scan with WebSocket price cache check."""
    
    # Verify WebSocket is running
    try:
        from app.services.simple_websocket import get_websocket_service
        ws_service = get_websocket_service()
        if not ws_service.is_streaming:
            logger.warning("⚠️ WebSocket not streaming - starting it now")
            ws_service.start_streaming()
    except Exception as e:
        logger.error(f"WebSocket check failed: {e}")
    
    # Continue with scan...
```

---

## 🧪 **Testing Checklist**

### **Test 1: P&L Exit Logic**
```bash
# 1. Create test position
sqlite3 trader.db "UPDATE bots SET current_position_size=100, current_position_entry_price=0.50 WHERE id=54;"

# 2. Simulate price at take-profit level
# Set current price to $0.65 (30% above entry $0.50)
# Run evaluation - should trigger TAKE_PROFIT

# 3. Simulate price at stop-loss level
# Set current price to $0.46 (-8% below entry $0.50)
# Run evaluation - should trigger STOP_LOSS

# 4. Check logs
grep "TAKE_PROFIT\|STOP_LOSS" logs/backend.log
```

### **Test 2: Multi-Timeframe Analysis**
```python
# Run test scan with timeframe analysis
python test_breakout_scanner.py

# Expected output:
# TRAC-USD: EARLY_STAGE, ACCELERATING → +15 bonus
# ASM-USD: LATE_STAGE, DECELERATING → -20 penalty
```

### **Test 3: MarketDataService Integration**
```bash
# 1. Clear Redis cache
redis-cli FLUSHDB

# 2. Run scan
python test_breakout_scanner.py

# 3. Check cache stats
curl "http://localhost:8000/api/v1/cache/stats" | jq

# Expected: High cache miss first run, high cache hit second run
```

### **Test 4: Rate Limiting**
```bash
# Run scanner 10 times in quick succession
for i in {1..10}; do
    python test_breakout_scanner.py
    sleep 1
done

# Check for rate limit errors
grep "rate limit" logs/backend.log
# Expected: ZERO rate limit errors (uses cache)
```

---

## 📋 **Implementation Order**

**Phase 1: Critical Fixes** (Do BEFORE enabling auto-trading)
1. ✅ Fix #3 - Route through MarketDataService (prevent rate limits)
2. ✅ Fix #4 - Verify WebSocket streaming active
3. ✅ Fix #1 - Add P&L exit logic (protect profits)
4. ⏳ Test all three fixes thoroughly

**Phase 2: Enhancement** (Can do during 48h validation)
5. ⏳ Fix #2 - Add multi-timeframe analysis (improve detection quality)
6. ⏳ Test timeframe analysis with live data
7. ⏳ Monitor 48h validation results

**Phase 3: Deployment** (After validation)
8. ⏳ Enable Celery Beat schedule (logging-only)
9. ⏳ Monitor for 48 hours
10. ⏳ Enable auto-trading if validation successful

---

## 🚨 **CRITICAL WARNING**

**DO NOT** enable auto-trading (`create_bots=True`) until:
- ✅ P&L exit logic implemented and tested
- ✅ MarketDataService integration complete
- ✅ WebSocket streaming verified active
- ✅ Rate limiting eliminated
- ✅ 48-hour validation shows good detection quality

**Why**: Current system would:
1. ❌ Hit rate limits (breaking other bots)
2. ❌ Never take profits (Oct 10 repeat)
3. ❌ Create bots for stale breakouts (poor timing)

---

## 📊 **Current System State**

```
Backend: ✅ Running
WebSocket: ❓ Unknown (need to verify)
Breakout Scanner: ✅ Implemented
P&L Exits: ❌ NOT IMPLEMENTED
Multi-Timeframe: ❌ NOT IMPLEMENTED
MarketDataService: ❌ NOT INTEGRATED
Auto-Trading: ❌ DISABLED (correct state)

Breakout Bots Created: 2 (TRAC-USDC, ASM-USDC)
Status: STOPPED (safe - awaiting manual activation)
```

---

**Next Action**: Implement Fix #3 (MarketDataService) and Fix #1 (P&L exits) before proceeding.
