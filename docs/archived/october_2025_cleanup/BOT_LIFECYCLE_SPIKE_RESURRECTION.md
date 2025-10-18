# Bot Lifecycle: Spike Detection & Resurrection Logic
**Date:** October 12, 2025  
**Status:** Design Clarification  
**Critical Question:** "If a spike is detected in one of these pairs marked with soft delete, will it start trading again?"

---

## Current Behavior (Before Refactoring)

**Trading Task Filter:**
```python
# backend/app/tasks/trading_tasks.py (line 30)
active_bots = db.query(Bot).filter(Bot.status == "RUNNING").all()

# Only RUNNING bots are evaluated
# STOPPED bots = ignored (no signal evaluation)
```

**Result:** If bot is STOPPED or ARCHIVED, it **never sees spikes**. Zero chance of trading.

---

## Problem with Naive Soft Delete

**Scenario:**
```
Day 1: BTC-USD bot stops trading (unprofitable)
Day 7: Bot archived (lifecycle_stage = "ARCHIVED")
Day 8: BTC breakout detected (+25% spike!) 🚀
Day 8: Archived bot MISSES opportunity 💔
```

**Why This Happens:**
```python
# Trading task still filters by status:
active_bots = db.query(Bot).filter(Bot.status == "RUNNING").all()

# Archived bot has status = "STOPPED"
# Never evaluated = never sees spike
```

---

## Solution Options

### **Option A: Resurrection Logic** 🔄 RECOMMENDED

**Concept:** Archived bots can be "woken up" by breakout scanner.

**Implementation:**

**Step 1: Breakout Scanner Checks Archived Bots**
```python
# backend/app/services/breakout_detector.py

def scan_with_resurrection_check(self, db: Session) -> Dict:
    """
    Scan for breakouts AND check if any match archived bots.
    If spike detected in archived pair → resurrect bot.
    """
    breakouts = self.scan_all_products()
    
    resurrected_bots = []
    
    for opportunity in breakouts:
        # Check if we have archived bot for this pair
        archived_bot = db.query(Bot).filter(
            Bot.pair == opportunity.product_id,
            Bot.lifecycle_stage == "ARCHIVED",
            Bot.archived_at < datetime.utcnow() - timedelta(hours=24)  # Grace period
        ).first()
        
        if archived_bot and opportunity.confidence in ["HIGH", "MEDIUM"]:
            # RESURRECT: Move back to ACTIVE
            archived_bot.lifecycle_stage = "ACTIVE"
            archived_bot.status = "RUNNING"
            archived_bot.archived_at = None
            
            logger.info(
                f"🔄 RESURRECTED bot {archived_bot.id} for {archived_bot.pair} "
                f"due to {opportunity.confidence} breakout (score={opportunity.score})"
            )
            
            resurrected_bots.append({
                "bot_id": archived_bot.id,
                "pair": archived_bot.pair,
                "reason": f"{opportunity.confidence} breakout",
                "score": opportunity.score
            })
    
    return {
        "new_breakouts": len(breakouts),
        "resurrected_bots": len(resurrected_bots),
        "resurrections": resurrected_bots
    }
```

**Step 2: Lifecycle Service Handles Resurrection**
```python
# backend/app/services/bot_lifecycle_service.py

class BotLifecycleService:
    
    def can_resurrect(self, bot: Bot) -> bool:
        """Check if bot is eligible for resurrection."""
        if bot.lifecycle_stage != "ARCHIVED":
            return False
        
        # Must be archived for at least 24 hours (cooling period)
        if not bot.archived_at:
            return False
        
        hours_archived = (datetime.utcnow() - bot.archived_at).total_seconds() / 3600
        if hours_archived < 24:
            return False
        
        # Must have learning data (makes resurrection valuable)
        if bot.signal_prediction_count < 100:  # Need meaningful history
            return False
        
        return True
    
    def resurrect_bot(
        self, 
        bot: Bot, 
        reason: str,
        breakout_score: float,
        db: Session
    ) -> Dict:
        """
        Resurrect archived bot back to ACTIVE trading.
        Preserves all learning data.
        """
        if not self.can_resurrect(bot):
            raise ValueError(f"Bot {bot.id} not eligible for resurrection")
        
        # Move back to ACTIVE
        bot.lifecycle_stage = "ACTIVE"
        bot.status = "RUNNING"
        bot.archived_at = None
        
        # Reset position state (clean slate)
        bot.current_position_size = 0.0
        bot.current_position_entry_price = None
        
        # Log resurrection event
        logger.info(
            f"🔄 RESURRECTED bot {bot.id} ({bot.pair}) - "
            f"Reason: {reason} | Score: {breakout_score} | "
            f"Learning: {bot.signal_prediction_count} predictions preserved"
        )
        
        db.commit()
        
        return {
            "bot_id": bot.id,
            "pair": bot.pair,
            "lifecycle_stage": "ACTIVE",
            "status": "RUNNING",
            "reason": reason,
            "learning_preserved": True,
            "predictions_available": bot.signal_prediction_count
        }
```

**Step 3: Update Celery Task**
```python
# backend/app/tasks/trading_tasks.py

@celery_app.task(name="app.tasks.trading_tasks.scan_for_breakouts")
def scan_for_breakouts(create_bots: bool = False, min_confidence: str = "MEDIUM"):
    """
    Scan for breakouts AND check for resurrection opportunities.
    """
    db = SessionLocal()
    try:
        detector = get_breakout_detector()
        
        # ENHANCED: Check for resurrections
        results = detector.scan_with_resurrection_check(db)
        
        logger.info(
            f"🔍 Breakout scan complete: "
            f"{results['new_breakouts']} breakouts, "
            f"{results['resurrected_bots']} bots resurrected"
        )
        
        # ... rest of existing logic ...
        
        return results
    finally:
        db.close()
```

**Benefits:**
- ✅ Archived bots can "wake up" for good opportunities
- ✅ Preserves all learning (1M+ predictions stay intact)
- ✅ Automatic (no manual intervention)
- ✅ Cooling period prevents thrashing (24h minimum)
- ✅ Quality filter (only resurrect if learning data exists)

**Lifecycle Flow with Resurrection:**
```
ACTIVE (trading)
  ↓ (P/L exit)
CLOSING (liquidating)
  ↓ (position closed)
CLOSED (cooldown 7 days)
  ↓ (auto-archive)
ARCHIVED (dormant)
  ↓ (breakout detected!) 🚀
ACTIVE (resurrected, trading again)
  ↓ (cycle repeats)
```

---

### **Option B: Permanent Archive (No Resurrection)** ❄️

**Concept:** Once archived, bot stays archived. Create NEW bot for spike.

**Implementation:**
```python
# Breakout scanner creates NEW bot even if archived one exists
def scan_for_breakouts(create_bots: bool = False):
    breakouts = detector.scan_all_products()
    
    for opportunity in breakouts:
        # Check if ACTIVE bot exists
        active_bot = db.query(Bot).filter(
            Bot.pair == opportunity.product_id,
            Bot.lifecycle_stage == "ACTIVE"
        ).first()
        
        if active_bot:
            continue  # Skip, already trading
        
        # Check if ARCHIVED bot exists
        archived_bot = db.query(Bot).filter(
            Bot.pair == opportunity.product_id,
            Bot.lifecycle_stage == "ARCHIVED"
        ).first()
        
        if archived_bot:
            # DON'T resurrect - create NEW bot instead
            new_bot = create_breakout_bot(
                db=db,
                product_id=opportunity.product_id,
                breakout_score=opportunity.score,
                signals=opportunity.signals
            )
            logger.info(
                f"Created NEW bot {new_bot.id} for {opportunity.product_id} "
                f"(archived bot {archived_bot.id} preserved)"
            )
        else:
            # No bot exists at all - create new
            create_breakout_bot(...)
```

**Benefits:**
- ✅ Simple logic (no resurrection complexity)
- ✅ Clear separation (old bot = archived, new bot = fresh start)
- ✅ Both learning datasets preserved

**Drawbacks:**
- ❌ Creates duplicate bots for same pair
- ❌ Doesn't leverage existing learning
- ❌ More database records over time

---

### **Option C: Hybrid - Smart Resurrection** 🧠 BEST OF BOTH

**Concept:** Resurrect if learning is valuable, create new if not.

**Implementation:**
```python
def handle_breakout_for_pair(
    self, 
    db: Session, 
    opportunity: BreakoutOpportunity
) -> Dict:
    """
    Intelligent decision: resurrect vs create new.
    """
    # Check for archived bot
    archived_bot = db.query(Bot).filter(
        Bot.pair == opportunity.product_id,
        Bot.lifecycle_stage == "ARCHIVED"
    ).first()
    
    if not archived_bot:
        # No archived bot - create new
        return create_breakout_bot(db, opportunity)
    
    # Evaluate if resurrection is worth it
    if self._should_resurrect(archived_bot, opportunity):
        # Has valuable learning - resurrect
        return self.lifecycle_service.resurrect_bot(
            bot=archived_bot,
            reason=f"{opportunity.confidence} breakout",
            breakout_score=opportunity.score,
            db=db
        )
    else:
        # Poor learning history - create fresh bot
        return create_breakout_bot(db, opportunity)

def _should_resurrect(
    self, 
    bot: Bot, 
    opportunity: BreakoutOpportunity
) -> bool:
    """
    Decide if bot should be resurrected vs creating new.
    """
    # Criteria 1: Has meaningful learning data
    if bot.signal_prediction_count < 100:
        return False  # Not enough data
    
    # Criteria 2: Historical performance
    if bot.total_pnl < -50.0:  # Lost more than $50
        return False  # Bad track record
    
    # Criteria 3: Not too old
    if bot.archived_at:
        days_archived = (datetime.utcnow() - bot.archived_at).days
        if days_archived > 30:
            return False  # Too stale
    
    # Criteria 4: Breakout quality
    if opportunity.confidence == "LOW":
        return False  # Don't waste resurrection on weak signals
    
    # All checks passed - resurrect!
    return True
```

**Benefits:**
- ✅ Best of both worlds
- ✅ Leverages good learning, discards bad
- ✅ Prevents "zombie bots" (poor performers)
- ✅ Quality-focused (only resurrect winners)

---

## Recommended Approach

### **Use Option C: Hybrid Smart Resurrection** 🎯

**Why:**
1. **Leverage Learning:** Good bots (BTC-USD with 1000+ predictions) get resurrected
2. **Fresh Starts:** Bad bots (lost money) get replaced with new ones
3. **Quality Control:** Only resurrect for MEDIUM+ breakouts
4. **Prevents Bloat:** Don't accumulate zombie bots

**Decision Tree:**
```
Spike detected in BTC-USD
  ↓
Check: Is there archived BTC-USD bot?
  ├─ NO → Create new bot ✅
  └─ YES → Evaluate archived bot:
      ├─ Has 100+ predictions? ✅
      ├─ Total P&L > -$50? ✅
      ├─ Archived < 30 days? ✅
      ├─ Breakout = MEDIUM+? ✅
      └─ ALL YES → RESURRECT 🔄
          ANY NO → Create new bot instead 🆕
```

---

## Implementation Changes

**Update Proposal Document:**
```python
# Add to Phase 3: Capital Reallocation Service

class CapitalReallocationService:
    
    def handle_breakout_opportunity(
        self, 
        db: Session, 
        opportunity: BreakoutOpportunity
    ) -> Dict:
        """
        Smart decision: resurrect archived bot OR create new.
        """
        # Check for archived bot
        archived_bot = db.query(Bot).filter(
            Bot.pair == opportunity.product_id,
            Bot.lifecycle_stage == "ARCHIVED"
        ).first()
        
        if archived_bot and self._should_resurrect(archived_bot, opportunity):
            # RESURRECT: Valuable learning exists
            return self.lifecycle_service.resurrect_bot(
                bot=archived_bot,
                reason=f"{opportunity.confidence} breakout",
                breakout_score=opportunity.score,
                db=db
            )
        else:
            # CREATE NEW: No archived bot OR poor performance
            return create_breakout_bot(
                db=db,
                product_id=opportunity.product_id,
                breakout_score=opportunity.score,
                signals=opportunity.signals
            )
```

**Benefits for Your Use Case:**
- ✅ Spike in archived BTC-USD → Resurrects if learned well
- ✅ Spike in archived AVNT-USD (-42% loser) → Creates fresh bot
- ✅ Spike in new pair (NEWCOIN-USD) → Creates new bot
- ✅ Capital automatically allocated to best opportunities

---

## Answer to Your Question

**Q: "If a spike is detected in one of these pairs marked with soft delete, will it start trading again?"**

**A: YES, with Smart Resurrection Logic!** 🚀

**Specifically:**
- **Good bots** (profitable, lots of learning) → RESURRECTED automatically
- **Bad bots** (unprofitable, poor learning) → NEW bot created instead
- **Cooling period:** 24h minimum before resurrection (prevents thrashing)
- **Quality filter:** Only MEDIUM+ breakouts trigger resurrection

**Example:**
```
BTC-USD bot archived (1000+ predictions, -$10 loss)
  ↓ (7 days later)
BTC spike detected (+20%, HIGH confidence)
  ↓ (resurrection check)
✅ Has learning: 1000 predictions
✅ Not terrible: Only -$10 loss
✅ Good breakout: HIGH confidence
  ↓
🔄 BOT RESURRECTED! Starts trading immediately
```

**vs**

```
AVNT-USD bot archived (50 predictions, -$42 loss)
  ↓ (7 days later)
AVNT spike detected (+15%, MEDIUM confidence)
  ↓ (resurrection check)
❌ Poor learning: Only 50 predictions
❌ Bad performance: -$42 loss
  ↓
🆕 NEW BOT CREATED instead (fresh start)
```

---

## Updated Timeline

**Phase 1:** Add lifecycle fields (2h)  
**Phase 2:** Auto-cleanup task (1h)  
**Phase 3:** Smart resurrection + capital reallocation (3h) ← ENHANCED  
**Phase 4:** Enable breakout scanner (30m)  
**Testing:** Integration + resurrection scenarios (1.5h)

**Total:** 8 hours (same as before, just better logic)

---

**Ready to implement with Smart Resurrection?** This gives you the best of both worlds! 🎯
