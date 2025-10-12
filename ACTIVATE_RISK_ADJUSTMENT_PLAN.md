# Activate RiskAdjustmentService - Implementation Plan

**Date**: October 11, 2025  
**Timeline**: 2-3 hours  
**Status**: Ready to implement NOW

---

## What We're Activating

**Existing Code**: `backend/app/services/risk_adjustment_service.py` (218 lines, fully implemented)

**What It Does**:
- Calculates dynamic position multiplier: **0.2x → 3.0x**
- Based on recent performance (last 50 trades)
- Based on signal strength + confidence
- Winners get scaled UP (toward 3.0x)
- Losers get scaled DOWN (toward 0.2x)

**Example Results**:
- **AVNT-USD** (winner): Gets 2.5x - 3.0x multiplier → More capital allocated
- **SQD-USD** (loser): Gets 0.2x - 0.5x multiplier → Less capital at risk

---

## Implementation Steps

### Step 1: Import RiskAdjustmentService (5 minutes)

**File**: `backend/app/services/bot_evaluator.py`

**Add import** at top of file:
```python
from .risk_adjustment_service import RiskAdjustmentService
```

**Initialize in `__init__`**:
```python
def __init__(self, db: Session):
    self.db = db
    # ... existing code ...
    self.risk_service = RiskAdjustmentService(db)  # ADD THIS
```

---

### Step 2: Calculate Risk Multiplier During Evaluation (10 minutes)

**File**: `backend/app/services/bot_evaluator.py`

**In `evaluate_bot()` method**, after signal calculation, before determining action:

```python
def evaluate_bot(self, bot: Bot) -> Dict[str, Any]:
    # ... existing signal calculation code ...
    
    # Calculate combined score
    combined_score = self._aggregate_signals(signal_results, weights)
    
    # NEW: Get risk multiplier from RiskAdjustmentService
    risk_data = self.risk_service.get_bot_risk_multiplier(
        bot_id=bot.id,
        product_id=bot.product_id,
        signal_strength=abs(combined_score),  # 0-1 range
        confidence=confidence  # From signal calculation
    )
    
    risk_multiplier = risk_data['risk_multiplier']  # 0.2 - 3.0
    
    # Log the risk assessment
    logger.info(
        f"🎲 {bot.product_id} Risk Assessment: {risk_multiplier:.2f}x "
        f"({risk_data['calculation_reason']})"
    )
    
    # ... rest of evaluation ...
```

---

### Step 3: Apply Multiplier to Position Sizing (15 minutes)

**Option A: In bot_evaluator.py `_determine_action()` method**

```python
def _determine_action(self, bot: Bot, combined_score: float, ..., risk_multiplier: float = 1.0) -> str:
    # ... existing code ...
    
    if action == "buy":
        # Apply risk multiplier to base position size
        base_size_usd = bot.initial_investment  # e.g., $20
        adjusted_size_usd = base_size_usd * risk_multiplier
        
        logger.info(
            f"💰 Position Sizing: Base ${base_size_usd} × {risk_multiplier:.2f} "
            f"= ${adjusted_size_usd:.2f}"
        )
        
        # Use adjusted_size_usd for trade execution
```

**Option B: In trading_service.py `execute_trade()` method**

```python
def execute_trade(self, bot: Bot, action: str, risk_multiplier: float = 1.0):
    # ... existing code ...
    
    # Apply risk multiplier
    base_size = bot.initial_investment
    adjusted_size = base_size * risk_multiplier
    
    # Execute with adjusted size
    order = self.place_order(product_id, action, adjusted_size)
```

---

### Step 4: Store Multiplier in Database (Optional - 20 minutes)

**Add field to Bot model** (if not exists):

```python
# backend/app/models/models.py
class Bot(Base):
    # ... existing fields ...
    current_risk_multiplier = Column(Float, default=1.0)  # ADD THIS
```

**Update after calculation**:
```python
bot.current_risk_multiplier = risk_multiplier
db.commit()
```

---

### Step 5: Test with Current Positions (30 minutes)

**Create test script**: `scripts/test_risk_service.py`

```python
#!/usr/bin/env python3
from backend.app.database import SessionLocal
from backend.app.models.models import Bot
from backend.app.services.risk_adjustment_service import RiskAdjustmentService

db = SessionLocal()
risk_service = RiskAdjustmentService(db)

# Get all active bots
bots = db.query(Bot).filter(Bot.is_active == True).all()

print("🎲 RISK MULTIPLIER ANALYSIS")
print("=" * 70)

for bot in bots:
    # Calculate risk multiplier
    risk_data = risk_service.get_bot_risk_multiplier(
        bot_id=bot.id,
        product_id=bot.product_id,
        signal_strength=0.5,  # Default for testing
        confidence=0.3        # Default for testing
    )
    
    multiplier = risk_data['risk_multiplier']
    performance = risk_data['performance_data']
    
    # Calculate position adjustment
    base_size = bot.initial_investment or 20
    new_size = base_size * multiplier
    
    print(f"{bot.product_id:12} | "
          f"Multiplier: {multiplier:.2f}x | "
          f"${base_size} → ${new_size:.2f} | "
          f"Avg P&L: ${performance['avg_pnl_per_trade']:.4f}")

db.close()
```

**Run test**:
```bash
python scripts/test_risk_service.py
```

---

### Step 6: Monitor First Results (1 hour)

**After integration, monitor logs**:
```bash
tail -f logs/backend.log | grep "Risk Assessment\|Position Sizing"
```

**Expected output**:
```
🎲 AVNT-USD Risk Assessment: 2.80x (HIGH signal (0.92) + MEDIUM confidence (0.32) + PROFITABLE performance ($0.1234/trade) → 2.80x risk (AGGRESSIVE))
💰 Position Sizing: Base $20 × 2.80 = $56.00

🎲 SQD-USD Risk Assessment: 0.35x (LOW signal (0.23) + LOW confidence (0.15) + LOSING performance ($-0.0456/trade) → 0.35x risk (DEFENSIVE))
💰 Position Sizing: Base $20 × 0.35 = $7.00
```

---

## Expected Impact

### Before Activation:
- All bots trade with same $20 position size
- Winners can't capitalize on success
- Losers continue bleeding at full size

### After Activation:
- **Winners** (like AVNT): $20 → $56 (2.8x) - Maximize gains
- **Losers** (like SQD): $20 → $7 (0.35x) - Minimize damage
- **Neutral bots**: Stay around $20 (1.0x)

### Portfolio Effect:
- Capital automatically flows from losers to winners
- Losing positions can't cause as much damage
- Winning positions can generate more profit
- Risk management happens automatically

---

## Implementation Checklist

### Phase 1: Basic Integration (1 hour)
- [ ] Add import to bot_evaluator.py
- [ ] Initialize RiskAdjustmentService in __init__
- [ ] Call get_bot_risk_multiplier() in evaluate_bot()
- [ ] Log risk multiplier results
- [ ] Test with one bot

### Phase 2: Position Sizing (30 minutes)
- [ ] Apply multiplier in _determine_action()
- [ ] OR apply multiplier in trading_service.execute_trade()
- [ ] Verify adjusted position sizes in logs

### Phase 3: Database Persistence (30 minutes)
- [ ] Add current_risk_multiplier field to Bot model
- [ ] Store multiplier after calculation
- [ ] Display in UI (optional)

### Phase 4: Testing & Validation (1 hour)
- [ ] Run test script on all bots
- [ ] Verify losers get reduced multipliers
- [ ] Verify winners get increased multipliers
- [ ] Monitor first few trades
- [ ] Check system errors (should be 0)

---

## Risk Assessment

### What Could Go Wrong?
1. **Over-scaling winners**: Max 3.0x prevents excessive risk
2. **Under-sizing losers**: Min 0.2x ensures we keep skin in game
3. **Calculation errors**: Service is already tested, just needs integration

### Safety Nets:
- ✅ Bounded multipliers (0.2x - 3.0x)
- ✅ Based on 50-trade rolling window (stable)
- ✅ Can disable by setting multiplier = 1.0
- ✅ Existing code is fully implemented and tested

### Rollback Plan:
```python
# If issues arise, simply comment out:
# risk_multiplier = risk_data['risk_multiplier']
risk_multiplier = 1.0  # Disable risk adjustment
```

---

## Why This is a Quick Win

1. **Code already exists** - No building from scratch
2. **Proven logic** - Formula is sound (signal + confidence + performance)
3. **Easy integration** - Just wire it into existing evaluation flow
4. **Immediate impact** - Starts working on next bot evaluation
5. **Low risk** - Can disable instantly if issues arise

---

## Next Steps After Activation

Once RiskAdjustmentService is working:

1. **Week 1**: Monitor performance, gather data
2. **Week 2**: Add emergency liquidation (-$40 threshold)
3. **Week 3**: Add momentum detection for scale-up
4. **Week 4**: Build HybridPortfolioDecisionEngine around it

But for NOW, just activate what exists! 🚀

---

## Ready to Proceed?

**Yes** - Start with Step 1 (5 minutes to add import)  
**No** - Review the code first and decide

**What do you want to do?**
