# Understanding Lifecycle Badges - What "ACTIVE" Means

**Date**: October 12, 2025  
**Question**: "What do these badges mean? They all have active"

## 📋 Quick Answer

**✅ ACTIVE** means your bot is **actively trading** and part of your live portfolio. This is the **normal, healthy state** for trading bots.

---

## 🔄 The Four Lifecycle Stages

The lifecycle badge system tracks the **automated capital management** lifecycle of each bot:

### 1. ✅ ACTIVE (What You're Seeing Now)
**Meaning**: Bot is actively trading in your portfolio

**What's Happening**:
- ✅ Bot evaluates signals every few minutes
- ✅ Bot executes trades when thresholds met
- ✅ Bot's P/L is monitored for exit triggers
- ✅ Capital is deployed and working

**When You See This**: 
- **All new bots** start as ACTIVE
- **All your current 32 bots** are ACTIVE
- This is the **normal state** for trading bots

**Exit Trigger**: Bot hits ±5% P/L threshold OR holds position for 7+ days

---

### 2. ⏳ CLOSING (You Haven't Seen This Yet)
**Meaning**: Bot hit exit trigger and is liquidating position

**What's Happening**:
- 🔄 Market sell order placed to close position
- 🔄 Waiting for order to fill
- 🔄 Bot stops evaluating new signals
- 🔄 Prepares to enter cooling period

**When You'll See This**:
- When bot hits **+10% take profit** (locks gains)
- When bot hits **-5% stop loss** (cuts losses)
- When bot holds position for **7+ days** (time limit)

**Duration**: Usually seconds to minutes (until order fills)

**Next Stage**: CLOSED (after position liquidated)

---

### 3. 🔒 CLOSED (Cooling Period - You Haven't Seen This Yet)
**Meaning**: Position closed, bot in 48-hour cooling period

**What's Happening**:
- 🕐 48-hour countdown timer running
- 💰 Capital freed but not yet reallocated
- 📊 System evaluates if bot should be resurrected or archived
- 🚫 Bot cannot trade during cooling period

**When You'll See This**:
- **After CLOSING stage completes**
- Badge shows: `🔒 CLOSED (48h)` with countdown

**Duration**: 48 hours (2 days)

**Next Stage**: Either ACTIVE (resurrected) or ARCHIVED

---

### 4. 📦 ARCHIVED (You Haven't Seen This Yet)
**Meaning**: Bot permanently retired, capital reallocated

**What's Happening**:
- 💸 Capital freed from this bot
- 🤖 Capital automatically reallocated to new bot
- 📚 Bot's learning data preserved
- 🔄 Bot can be resurrected if conditions improve

**When You'll See This**:
- **After 48-hour cooling period** (if not resurrected)
- Bot removed from active trading view
- Available in "Archived Bots" section

**Resurrection Possible If**:
- Bot has >100 signal predictions (learning history)
- Bot didn't lose more than $50
- Bot hasn't been archived >30 days

---

## 🎯 Why They're All "ACTIVE" Right Now

Your 32 bots are all showing **✅ ACTIVE** because:

1. **System Just Implemented** (October 12, 2025)
   - Lifecycle management system is brand new
   - No bots have hit P/L exit triggers yet
   - All bots initialized to ACTIVE state

2. **Normal Trading State**
   - Bots are trading normally
   - No positions have hit ±5% P/L thresholds
   - No positions held for 7+ days yet

3. **First Transitions Pending**
   - You'll see your first CLOSING badge when a bot hits:
     - +10% take profit, OR
     - -5% stop loss, OR
     - 7-day position hold time

---

## 📊 What Triggers State Changes?

### ACTIVE → CLOSING Triggers:
1. **Take Profit**: Position reaches +10% gain
2. **Stop Loss**: Position reaches -5% loss
3. **Time Limit**: Position held for 7+ days
4. **Manual Close**: User manually closes position

### CLOSING → CLOSED Triggers:
- **Automatic**: Position liquidated successfully
- **Immediate**: Usually within seconds/minutes

### CLOSED → ARCHIVED Triggers:
- **Automatic**: After 48-hour cooling period
- **Conditions**: Bot doesn't meet resurrection criteria

### CLOSED → ACTIVE (Resurrection) Triggers:
- **Automatic**: Bot meets resurrection criteria:
  - Has >100 signal predictions (learning history)
  - Lost less than $50 total
  - Archived less than 30 days
  - Been in cooling period at least 24 hours

---

## 🔮 What You'll See Soon

### First P/L Exit (Coming Soon)
When your first bot hits a P/L threshold:

1. **Badge changes**: ✅ ACTIVE → ⏳ CLOSING
2. **Position liquidates**: Market sell order executes
3. **Badge changes**: ⏳ CLOSING → 🔒 CLOSED (48h)
4. **Countdown starts**: Shows remaining hours
5. **After 48h**: 
   - Either: 🔒 CLOSED → ✅ ACTIVE (resurrected)
   - Or: 🔒 CLOSED → 📦 ARCHIVED (retired)

### Capital Reallocation
When bot is archived:
1. Capital freed from that bot ($20-$30 typically)
2. System scans for breakout opportunities
3. New bot automatically created for hot pair
4. New bot starts with ✅ ACTIVE badge

---

## 💡 Why This System Exists

**Problem**: Dead bots sitting on capital from old, stale positions

**Solution**: Automatic lifecycle management
- ✅ Locks profits at +10%
- ✅ Cuts losses at -5%
- ✅ Prevents capital from being stuck
- ✅ Automatically reallocates to new opportunities
- ✅ Preserves learning data for resurrection

**Benefit**: Capital always working, never stuck in losing positions

---

## 🎨 Badge Color Guide

| Stage | Badge | Color | Icon | Meaning |
|-------|-------|-------|------|---------|
| **ACTIVE** | ✅ Active | Green | ✅ | Trading normally |
| **CLOSING** | ⏳ Closing | Yellow | ⏳ | Liquidating position |
| **CLOSED** | 🔒 Closed (Xh) | Blue | 🔒 | Cooling period (countdown) |
| **ARCHIVED** | 📦 Archived | Gray | 📦 | Retired, capital freed |

---

## 🔍 How to Check Bot Lifecycle

### Current Bot Status
```bash
curl -s "http://localhost:8000/api/v1/bots/" | jq '[.[] | {pair, lifecycle_stage}] | .[0:5]'
```

**Your Output** (right now):
```json
[
  {"pair": "BTC-USD", "lifecycle_stage": "ACTIVE"},
  {"pair": "ETH-USD", "lifecycle_stage": "ACTIVE"},
  {"pair": "SOL-USD", "lifecycle_stage": "ACTIVE"}
  // ... all 32 bots are ACTIVE
]
```

### When to Expect Changes
- **First CLOSING**: When any bot hits ±5% P/L or 7-day hold
- **First CLOSED**: ~1 minute after CLOSING (order fills)
- **First ARCHIVED**: 48 hours after CLOSED (if not resurrected)

---

## Summary

### Right Now:
- ✅ All bots show **ACTIVE** badge (green)
- ✅ This is **normal and expected**
- ✅ Bots are trading normally

### Soon:
- ⏳ You'll see **CLOSING** badge (yellow) when first bot hits P/L exit
- 🔒 Then **CLOSED** badge (blue) with 48h countdown
- 📦 Finally **ARCHIVED** badge (gray) if bot doesn't get resurrected

### Purpose:
- 🔄 **Automated capital management**
- 💰 **Never sit on losing positions**
- 🎯 **Always reallocate to best opportunities**
- 📚 **Preserve learning for resurrection**

The lifecycle system is working correctly - you just haven't seen any exits yet because the system is new! When your first bot hits a P/L threshold, you'll see the badge change and the automated lifecycle management in action. 🚀
