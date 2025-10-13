# Bot Creation and Auto-Start Behavior

**Date**: October 12, 2025  
**Question**: "Are bots automatically started when added?"

## ❌ Answer: NO - Bots Are Created in STOPPED State

### Current Behavior

When you create a new bot via the API or UI:

1. **Bot is created with `status = "STOPPED"`** (database default)
2. **Bot has `lifecycle_stage = "ACTIVE"`** (ready to trade when started)
3. **Bot does NOT begin evaluating signals** (Celery tasks only process `status = "RUNNING"` bots)
4. **Manual start is required** to begin trading

---

## Bot Status vs Lifecycle Stage

These are **two separate concepts**:

### Status Field (Trading Control)
- **Purpose**: Controls whether bot evaluates signals and trades
- **Values**: `"RUNNING"` or `"STOPPED"`
- **Default**: `"STOPPED"` when created
- **Changed by**: Manual start/stop actions

### Lifecycle Stage (Capital Management)
- **Purpose**: Tracks bot lifecycle for auto-archival and capital reallocation
- **Values**: `"ACTIVE"`, `"CLOSING"`, `"CLOSED"`, `"ARCHIVED"`
- **Default**: `"ACTIVE"` when created
- **Changed by**: Automated P/L monitoring and lifecycle tasks

---

## Evidence from Code

### 1. Bot Model Default (models.py)
```python
class Bot(Base):
    __tablename__ = "bots"
    
    status = Column(String(20), default="STOPPED")  # ← Default is STOPPED
    lifecycle_stage = Column(String(20), default="ACTIVE")  # ← But lifecycle is ACTIVE
```

### 2. Create Bot Function (bots.py)
```python
@router.post("/", response_model=BotResponse)
def create_bot(bot: BotCreate, db: Session = Depends(get_db)):
    db_bot = Bot(
        name=bot.name,
        pair=bot.pair,
        # ... other fields ...
        # Note: status defaults to "STOPPED" from model definition
        # Note: lifecycle_stage defaults to "ACTIVE" from model definition
    )
    db.add(db_bot)
    db.commit()
    # Bot is now in database with status="STOPPED", lifecycle_stage="ACTIVE"
```

### 3. Celery Evaluation Task (trading_tasks.py)
```python
@celery_app.task(name="app.tasks.trading_tasks.evaluate_bot_signals")
def evaluate_bot_signals(enable_automatic_trading: bool = False):
    # Get all running bots (STOPPED bots are excluded!)
    active_bots = db.query(Bot).filter(Bot.status == "RUNNING").all()
    
    # Only RUNNING bots are evaluated for signals
    for bot in active_bots:
        result = evaluator.evaluate_bot(bot, market_data)
```

### 4. Start/Stop Endpoints
```python
@router.post("/{bot_id}/start")
def start_bot(bot_id: int, db: Session = Depends(get_db)):
    bot.status = "RUNNING"  # ← Manual action required
    db.commit()
    return {"message": f"Bot '{bot.name}' started successfully"}

@router.post("/{bot_id}/stop")
def stop_bot(bot_id: int, db: Session = Depends(get_db)):
    bot.status = "STOPPED"
    db.commit()
    return {"message": f"Bot '{bot.name}' stopped successfully"}
```

---

## Current Bot States

Checking your live system:

```bash
curl "http://localhost:8000/api/v1/bots/" | jq '[.[] | {pair, status, lifecycle_stage}] | .[0:3]'
```

**Result**: All your bots are **manually started**:
```json
[
  {
    "pair": "BTC-USD",
    "status": "RUNNING",        // ← Manually started
    "lifecycle_stage": "ACTIVE"
  },
  {
    "pair": "ETH-USD",
    "status": "RUNNING",        // ← Manually started
    "lifecycle_stage": "ACTIVE"
  },
  {
    "pair": "SOL-USD",
    "status": "RUNNING",        // ← Manually started
    "lifecycle_stage": "ACTIVE"
  }
]
```

---

## How to Start a New Bot

### Option 1: UI (if start button exists)
1. Create bot via "Create Bot" form
2. Find bot in bot list
3. Click "Start" button (▶️ icon)
4. Bot begins evaluating signals

### Option 2: API
```bash
# Create bot
curl -X POST "http://localhost:8000/api/v1/bots/" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "New Bot",
    "pair": "AVAX-USD",
    "position_size_usd": 25
  }'

# Get bot ID from response (e.g., id: 43)

# Start bot
curl -X POST "http://localhost:8000/api/v1/bots/43/start"
```

### Option 3: Bulk Start
```bash
# Start all STOPPED bots
curl -X POST "http://localhost:8000/api/v1/bots/start-all"
```

---

## Why This Design?

### Safety First
- **Prevents accidental trading** with unconfigured bots
- **Allows validation** before enabling live trades
- **Gives control** over when capital is deployed

### Separation of Concerns
- **Status**: "Am I trading right now?" (user control)
- **Lifecycle**: "What stage of my life am I in?" (automated management)

---

## Recommendation: Add Auto-Start Option?

If you want new bots to start automatically, we could add:

### Option A: Auto-start flag on creation
```python
@router.post("/", response_model=BotResponse)
def create_bot(bot: BotCreate, auto_start: bool = False, db: Session = Depends(get_db)):
    db_bot = Bot(...)
    db.add(db_bot)
    db.commit()
    
    if auto_start:
        db_bot.status = "RUNNING"
        db.commit()
    
    return prepare_bot_response(db_bot)
```

### Option B: UI checkbox
```tsx
<BotForm>
  <input type="checkbox" checked={autoStart} onChange={...} />
  <label>Start bot immediately after creation</label>
</BotForm>
```

### Option C: Default to RUNNING
```python
# In models.py
status = Column(String(20), default="RUNNING")  # ← Change default
```

---

## Current Workflow

**Creating a Bot**:
1. User fills out "Create Bot" form
2. Bot created with `status="STOPPED"`, `lifecycle_stage="ACTIVE"`
3. Bot appears in UI with ⏸️ STOPPED indicator
4. User clicks "Start" button
5. Bot status changes to `status="RUNNING"`
6. Celery task picks up bot on next evaluation cycle
7. Bot begins trading

**Your 32 Active Bots**:
- All have been manually started at some point
- All are currently `status="RUNNING"`
- All are `lifecycle_stage="ACTIVE"` (ready for lifecycle management)

---

## Summary

❌ **No**, bots are **not automatically started** when created  
✅ **Yes**, they must be **manually started** via API or UI  
✅ **Yes**, this is by design for safety and control  
✅ **Yes**, we can add auto-start if you want it  

Your 32 current bots are all running because you (or the system) started them manually after creation.
