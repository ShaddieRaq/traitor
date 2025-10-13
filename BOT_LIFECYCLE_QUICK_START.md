# Bot Lifecycle - Quick Reference
**Date:** October 12, 2025

## Immediate Next Steps

```bash
# 1. Restart services (apply changes)
./scripts/stop.sh && ./scripts/start.sh

# 2. Verify lifecycle fields created
curl -s "http://localhost:8000/api/v1/bots/" | jq '.[0] | {lifecycle_stage, archived_at}'

# 3. Monitor first P/L exits (within 10 minutes)
tail -f logs/backend.log | grep -E "(P/L PROTECTION|lifecycle)"
```

---

## Lifecycle Flow

```
ACTIVE → CLOSING → CLOSED (7 days) → ARCHIVED → RESURRECTED (if spike)
```

---

## What Was Built

| Component | File | Purpose |
|-----------|------|---------|
| Model | `models.py` | Added 3 lifecycle columns |
| Service | `bot_lifecycle_service.py` | State transitions + resurrection |
| Service | `capital_reallocation_service.py` | Smart bot creation/resurrection |
| Tasks | `lifecycle_tasks.py` | Daily cleanup + capital reallocation |
| Integration | `bot_evaluator.py` | P/L exits trigger transitions |
| Scanner | `trading_tasks.py` | Smart resurrection in breakout scanner |
| Schedule | `celery_app.py` | 3 new scheduled tasks |

---

## Automated Tasks

| Task | Schedule | Purpose |
|------|----------|---------|
| `breakout-scanner` | Every 2 hours | Find opportunities, create/resurrect bots |
| `check-closing-bots` | Every 1 hour | Transition CLOSING → CLOSED |
| `daily-bot-cleanup` | Daily 2 AM UTC | Archive old bots + reallocate capital |

---

## Key Features

✅ **Auto-Create**: Breakout scanner creates up to 2 bots every 2 hours  
✅ **Auto-Delete**: Bots archived 7 days after position closes  
✅ **Smart Resurrection**: Archived bots with 100+ predictions get resurrected on spikes  
✅ **Capital Reallocation**: Freed capital ($240+) automatically allocated to new opportunities  
✅ **Learning Preservation**: All 1M+ predictions stay intact

---

## Safeguards

- Max 2 bots per scan (not 5+)
- Max 10 breakout bots total
- 7-day cooling period before archive
- 24-hour minimum before resurrection
- Only MEDIUM+ confidence breakouts
- Capital availability checks

---

## Expected Results

**Today:** 2 take profits + 12 stop losses execute → 12 bots to CLOSING/CLOSED  
**Day 7:** 12 bots archived → $240 freed  
**Day 7 (2 AM):** 2 new breakout bots created  
**Week 2:** First resurrections if spikes detected  

---

## Monitor

```bash
# Lifecycle distribution
curl -s "http://localhost:8000/api/v1/bots/" | \
  jq '[.[] | .lifecycle_stage] | group_by(.) | map({stage: .[0], count: length})'

# Freed capital
curl -s "http://localhost:8000/api/v1/bots/" | \
  jq '[.[] | select(.lifecycle_stage == "ARCHIVED")] | map(.position_size_usd) | add'

# Logs
grep "lifecycle" logs/backend.log | tail -20
grep "RESURRECTED" logs/backend.log
grep "Daily cleanup" logs/celery-worker.log
```

---

## If Issues Arise

```bash
# Disable auto-creation (edit celery_app.py)
"breakout-scanner": {
    "kwargs": {"create_bots": False}  # Change to False
}

# Restart
./scripts/restart.sh
```

All learning data preserved - zero risk! 🛡️
