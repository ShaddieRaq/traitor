# Bot Lifecycle Refactoring Proposal
**Date:** October 12, 2025  
**Status:** Proposal - Awaiting User Decision  
**Priority:** HIGH - Enables dynamic capital reallocation

## Problem Statement

**User Need:** "I need auto create and delete of bots. I don't just want to sit in these old trades. I rather free this capital for the new bots."

**Current State:**
- 30 RUNNING bots, 24 with open positions (capital locked)
- No automatic bot creation (despite breakout scanner existing)
- No automatic bot deletion (bots accumulate forever)
- Manual management required for bot lifecycle

**Architectural Issue:**
```python
# Bot.id is auto-increment Integer (1, 2, 3...)
class Bot(Base):
    id = Column(Integer, primary_key=True)
    pair = Column(String(20), index=True)  # NOT unique!

# Foreign key dependencies (breaks learning when deleted):
class BotSignalHistory(Base):
    bot_id = Column(Integer, ForeignKey("bots.id"))

class Trade(Base):
    bot_id = Column(Integer, ForeignKey("bots.id"))

class AdaptiveSignalWeights(Base):
    bot_id = Column(Integer, ForeignKey("bots.id"))

class SignalPredictionRecord(Base):
    bot_id = Column(Integer, ForeignKey("bots.id"))  # 1M+ records!
```

**The Core Problem:**
- Multiple bots can exist for same pair (BTC-USD bot #3, #42, #89...)
- Deleting bot breaks foreign keys → loses 1M+ prediction records
- Can't reuse bot_id (auto-increment)
- Can't use pair as key (not unique, multiple bots per pair by design)

---

## Current Capital Allocation

**Portfolio Snapshot:**
- 30 RUNNING bots
- 24 bots with open positions (80% capital locked)
- Positions preview from earlier:
  - 2 take profits ready: +$86 profit
  - 12 stop losses ready: -$91 losses to cut
  - 7 holds: monitoring
  - 2 unprotected: no entry price

**Capital Opportunity Cost:**
- Old losing positions (AVNT -42%, FLOKI -31%) tying up $20/bot
- Could reallocate to new breakout opportunities
- Breakout scanner exists but disabled (no cleanup mechanism)

---

## Solution Options

### **Option 1: Soft Delete with Learning Preservation** ✅ RECOMMENDED

**Concept:** Add lifecycle states without breaking foreign keys.

**Implementation:**
```python
# Model changes (NO migration needed - add columns):
class Bot(Base):
    status = Column(String(20), default="STOPPED")  # Existing
    lifecycle_stage = Column(String(20), default="ACTIVE")  # NEW
    # ACTIVE → CLOSING → CLOSED → ARCHIVED → DELETED
    
    archived_at = Column(DateTime(timezone=True))  # NEW
    deletion_scheduled_at = Column(DateTime(timezone=True))  # NEW
    
    # Deletion rules
    can_auto_delete = Column(Boolean, default=True)  # NEW
    preserve_learning = Column(Boolean, default=True)  # NEW
```

**Lifecycle Flow:**
```
ACTIVE (bot trading)
  ↓ (P/L exit triggered OR manual stop)
CLOSING (liquidating position)
  ↓ (position closed)
CLOSED (position = 0, cooldown period)
  ↓ (7 days + no activity)
ARCHIVED (soft deleted, learning preserved)
  ↓ (30 days + user confirmed)
DELETED (hard delete, cascade to all tables)
```

**Benefits:**
- ✅ Zero migration complexity
- ✅ Preserves all learning data
- ✅ Reversible (can unarchive)
- ✅ Gradual cleanup (not sudden)
- ✅ User can override (preserve_learning=True)

**Auto-Cleanup Task:**
```python
@celery_app.task(name="lifecycle.cleanup_bots")
def cleanup_bot_lifecycle():
    """
    Daily bot lifecycle management:
    1. Move CLOSED bots to ARCHIVED after 7 days
    2. Hard delete ARCHIVED bots after 30 days (if preserve_learning=False)
    3. Free capital from ARCHIVED bots for reallocation
    """
    # Celery Beat: Every 24 hours
```

**Capital Reallocation:**
```python
# When bot moves CLOSED → ARCHIVED:
# 1. Sum up freed capital: archived_bot.position_size_usd
# 2. Check breakout opportunities
# 3. Create new BREAKOUT bots with freed capital
# 4. Result: Dynamic portfolio rotation
```

---

### **Option 2: Composite Key Migration** ⚠️ COMPLEX

**Concept:** Use (pair, trading_mode, sequence) as composite primary key.

**Implementation:**
```python
class Bot(Base):
    # OLD: id = Column(Integer, primary_key=True)
    # NEW: Composite key
    pair = Column(String(20), primary_key=True)
    trading_mode = Column(String(20), primary_key=True)
    sequence = Column(Integer, primary_key=True, default=1)
    
    # Example: ("BTC-USD", "CORE", 1), ("BTC-USD", "BREAKOUT", 1)
```

**Migration Required:**
```sql
-- Drop all foreign keys
-- Recreate bots table with composite key
-- Migrate 1M+ SignalPredictionRecord rows
-- Recreate all foreign keys
-- Update all API endpoints
-- Update all frontend code
```

**Benefits:**
- ✅ Semantic keys (meaningful identifiers)
- ✅ Prevents duplicate pair+mode combinations
- ✅ Can reuse bot identity after deletion

**Drawbacks:**
- ❌ Major migration (high risk)
- ❌ 1M+ rows need updating
- ❌ API breaking change
- ❌ Frontend breaking change
- ❌ 2-3 days implementation + testing

---

### **Option 3: Bot Pooling Pattern** 🔄 INNOVATIVE

**Concept:** Reuse bot entities instead of creating/deleting.

**Implementation:**
```python
class BotPool:
    """
    Manages bot lifecycle through reuse pattern:
    - Create N bots per pair (e.g., 3 slots)
    - Assign bots to opportunities
    - Release bots when done
    - Reuse released bots for new opportunities
    """
    
    @staticmethod
    def get_available_bot(pair: str, trading_mode: str) -> Bot:
        """Get or create bot for opportunity."""
        # Try to find released bot
        bot = db.query(Bot).filter(
            Bot.pair == pair,
            Bot.trading_mode == trading_mode,
            Bot.lifecycle_stage == "AVAILABLE"
        ).first()
        
        if bot:
            # Reuse existing bot
            bot.lifecycle_stage = "ASSIGNED"
            return bot
        else:
            # Create new bot (up to max_bots_per_pair)
            return create_new_bot(pair, trading_mode)
    
    @staticmethod
    def release_bot(bot: Bot):
        """Release bot back to pool after position closes."""
        bot.lifecycle_stage = "AVAILABLE"
        bot.current_position_size = 0
        bot.current_position_entry_price = None
        # Keep all learning data intact!
```

**Lifecycle States:**
```
AVAILABLE (in pool, ready for assignment)
  ↓ (breakout detected)
ASSIGNED (active opportunity, trading)
  ↓ (P/L exit OR time limit)
CLOSING (liquidating position)
  ↓ (position closed)
AVAILABLE (back in pool, learning preserved)
```

**Benefits:**
- ✅ Zero deletions (infinite learning accumulation)
- ✅ Instant bot availability (no creation lag)
- ✅ Learning compounds across opportunities
- ✅ Simple implementation (no migration)

**Drawbacks:**
- ⚠️ Need max_bots_per_pair limit
- ⚠️ Pool management complexity

---

## Recommended Implementation Plan

### **Phase 1: Soft Delete Foundation** (2 hours)

**Step 1: Add lifecycle fields (NO migration)**
```python
# backend/app/models/models.py
class Bot(Base):
    lifecycle_stage = Column(String(20), default="ACTIVE")
    archived_at = Column(DateTime(timezone=True))
    can_auto_delete = Column(Boolean, default=True)
```

**Step 2: Create lifecycle service**
```python
# backend/app/services/bot_lifecycle_service.py
class BotLifecycleService:
    def transition_to_closing(self, bot: Bot):
        """Move to CLOSING when P/L exit triggered."""
    
    def transition_to_closed(self, bot: Bot):
        """Move to CLOSED when position = 0."""
    
    def transition_to_archived(self, bot: Bot):
        """Move to ARCHIVED after 7 days closed."""
    
    def get_freed_capital(self) -> float:
        """Calculate capital freed from archived bots."""
```

**Step 3: Update bot_evaluator.py**
```python
# After P/L exit executes:
if trade_executed:
    lifecycle_service.transition_to_closing(bot)
    # After position confirmed closed:
    lifecycle_service.transition_to_closed(bot)
```

---

### **Phase 2: Auto-Cleanup Task** (1 hour)

```python
# backend/app/tasks/lifecycle_tasks.py
@celery_app.task(name="lifecycle.daily_cleanup")
def daily_bot_lifecycle_cleanup():
    """
    Daily bot lifecycle management.
    Runs at 2:00 AM UTC.
    """
    db = SessionLocal()
    try:
        # Move CLOSED → ARCHIVED (after 7 days)
        closed_bots = db.query(Bot).filter(
            Bot.lifecycle_stage == "CLOSED",
            Bot.updated_at < datetime.utcnow() - timedelta(days=7)
        ).all()
        
        for bot in closed_bots:
            bot.lifecycle_stage = "ARCHIVED"
            bot.archived_at = datetime.utcnow()
            logger.info(f"📦 Archived bot {bot.id} ({bot.pair}) - freed ${bot.position_size_usd}")
        
        db.commit()
        
        # Calculate freed capital
        freed_capital = sum(b.position_size_usd for b in closed_bots)
        
        return {
            "bots_archived": len(closed_bots),
            "capital_freed": freed_capital
        }
    finally:
        db.close()

# Add to celery_app.py beat_schedule:
"daily-bot-cleanup": {
    "task": "lifecycle.daily_cleanup",
    "schedule": crontab(hour=2, minute=0)  # 2 AM UTC
}
```

---

### **Phase 3: Auto-Creation with Capital Reallocation** (2 hours)

```python
# backend/app/services/capital_reallocation_service.py
class CapitalReallocationService:
    def get_available_capital(self, db: Session) -> float:
        """Calculate capital available for new bots."""
        # Freed capital from archived bots
        archived_capital = db.query(func.sum(Bot.position_size_usd)).filter(
            Bot.lifecycle_stage == "ARCHIVED"
        ).scalar() or 0.0
        
        # User's total allocation (e.g., $500)
        total_allocation = 500.0
        
        # Currently deployed capital
        active_capital = db.query(func.sum(Bot.position_size_usd)).filter(
            Bot.lifecycle_stage.in_(["ACTIVE", "CLOSING"])
        ).scalar() or 0.0
        
        available = total_allocation - active_capital + archived_capital
        return max(0.0, available)
    
    def create_breakout_bots_from_freed_capital(self, db: Session):
        """Create new breakout bots using freed capital."""
        available = self.get_available_capital(db)
        
        if available < 15.0:  # Minimum for one bot
            logger.info(f"Insufficient capital for new bots: ${available:.2f}")
            return
        
        # Get breakout opportunities
        from ..services.breakout_detector import get_breakout_detector
        detector = get_breakout_detector()
        breakouts = detector.scan_all_products()
        
        # Create bots with available capital
        bots_to_create = int(available / 15.0)  # $15 per bot
        
        for i, opportunity in enumerate(breakouts[:bots_to_create]):
            create_breakout_bot(
                db=db,
                product_id=opportunity.product_id,
                breakout_score=opportunity.score,
                signals=opportunity.signals,
                initial_investment=15.0
            )
            logger.info(f"🚀 Created breakout bot with freed capital: {opportunity.product_id}")

# Add to daily cleanup task:
@celery_app.task(name="lifecycle.daily_cleanup")
def daily_bot_lifecycle_cleanup():
    # ... archive bots ...
    
    # Reallocate freed capital
    reallocation_service = CapitalReallocationService()
    reallocation_service.create_breakout_bots_from_freed_capital(db)
```

---

### **Phase 4: Enable Breakout Scanner** (30 minutes)

```python
# backend/app/tasks/celery_app.py
beat_schedule={
    # ... existing tasks ...
    
    # NEW: Controlled breakout scanning
    "breakout-scanner": {
        "task": "app.tasks.trading_tasks.scan_for_breakouts",
        "schedule": 7200.0,  # Every 2 hours (not 10 minutes!)
        "kwargs": {
            "create_bots": True,  # Auto-create enabled
            "min_confidence": "MEDIUM"  # Only medium+ opportunities
        }
    },
    
    # NEW: Daily lifecycle cleanup + capital reallocation
    "daily-bot-cleanup": {
        "task": "lifecycle.daily_cleanup",
        "schedule": crontab(hour=2, minute=0)  # 2 AM UTC
    }
}
```

**Safeguards:**
```python
# In scan_for_breakouts task:
MAX_BREAKOUT_BOTS = 10  # Limit total BREAKOUT bots
MAX_NEW_BOTS_PER_SCAN = 2  # Max 2 bots per scan

# Check limits before creating:
existing_breakout_count = db.query(Bot).filter(
    Bot.trading_mode == "BREAKOUT",
    Bot.lifecycle_stage.in_(["ACTIVE", "CLOSING"])
).count()

if existing_breakout_count >= MAX_BREAKOUT_BOTS:
    logger.info(f"Max breakout bots reached ({MAX_BREAKOUT_BOTS}), skipping creation")
    return
```

---

## Expected Outcomes

### **Immediate Benefits** (Week 1)

**Before (Current State):**
- 30 bots, 24 with open positions
- Manual management only
- Capital locked in old losing trades (AVNT -42%, FLOKI -31%)
- No breakout opportunities captured

**After (With Refactoring):**
- 30 bots → dynamic (25 CORE + 5-10 BREAKOUT rotating)
- 12 losing positions cut (free ~$240 capital)
- 2 profitable exits locked (+$86 profit)
- Freed capital auto-allocated to new breakouts
- Zero manual management required

### **Long-Term Benefits** (Month 1)

**Portfolio Dynamics:**
- **CORE bots** (25): Long-term positions, learning accumulation
- **BREAKOUT bots** (5-10): Short-term momentum, high turnover
- **Lifecycle**: Auto-cleanup after 7 days → capital reallocation
- **Learning**: All data preserved (1M+ predictions compound)

**Capital Efficiency:**
- Old: 80% capital locked in stale positions
- New: 50% active, 30% rotating (breakouts), 20% available (freed)
- Result: Higher opportunities captured per dollar

**Performance Tracking:**
```
Week 1: 12 stop losses cut, 2 take profits locked
Week 2: 3 new breakout bots created (freed capital)
Week 3: 2 breakout bots archived (positions closed), 2 new created
Week 4: Portfolio rebalanced, learning preserved, capital optimized
```

---

## Implementation Timeline

**Total: 1 day (8 hours)**

| Phase | Time | Description |
|-------|------|-------------|
| Phase 1 | 2h | Add lifecycle fields + service |
| Phase 2 | 1h | Create auto-cleanup task |
| Phase 3 | 2h | Build capital reallocation |
| Phase 4 | 30m | Enable breakout scanner |
| Testing | 1h | Integration testing |
| Validation | 1.5h | Monitor first lifecycle |

**Risk Level:** LOW
- No database migration required
- Additive changes only (no breaking changes)
- Can rollback easily (disable tasks)
- Preserves all learning data

---

## Decision Required

**Which solution do you prefer?**

1. **Option 1: Soft Delete** ✅ (Recommended - fastest, safest)
   - Implementation: 1 day
   - Risk: LOW
   - Learning: Preserved
   - Capital: Dynamic reallocation

2. **Option 2: Composite Key** ⚠️ (Major refactor)
   - Implementation: 2-3 days
   - Risk: HIGH
   - Learning: Preserved (with migration)
   - Capital: Manual management

3. **Option 3: Bot Pooling** 🔄 (Innovative)
   - Implementation: 1.5 days
   - Risk: MEDIUM
   - Learning: Maximum accumulation
   - Capital: Auto-managed

**My Recommendation:** Start with **Option 1** (soft delete) because:
- Fastest to implement (1 day)
- Lowest risk (no migration)
- Achieves your goal (auto create/delete + capital freedom)
- Can evolve to Option 3 later if desired

**Next Step:** Confirm your choice, and I'll implement immediately! 🚀
