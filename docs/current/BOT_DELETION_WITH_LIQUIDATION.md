# Bot Deletion with Liquidation Feature

**Status**: ✅ COMPLETED (October 9, 2025)  
**Author**: AI Agent  
**Feature**: Delete bots with optional automatic liquidation of holdings

---

## Overview

The bot deletion feature allows users to delete trading bots with an optional automatic liquidation of all holdings for that trading pair. This prevents orphaned positions and provides a clean exit strategy.

## User Experience

### Frontend UI
- **Location**: Dashboard → Bot Cards → Delete Button
- **Modal**: Confirmation dialog with liquidation checkbox (defaulted to **checked**)
- **Checkbox Options**:
  - ✅ **Liquidate holdings** (default): Sells all holdings before deleting bot
  - ❌ **Delete only**: Removes bot but keeps holdings in account

### User Flow
1. Click delete button on any bot card
2. Modal appears with bot name and liquidation option
3. Liquidation checkbox is **pre-checked** by default (recommended)
4. Click "Liquidate & Delete" or "Delete Bot"
5. Trade executes on Coinbase (if holdings exist and liquidation enabled)
6. Bot is deleted from database
7. Modal closes automatically
8. Bot disappears from UI immediately (optimistic update)

---

## Technical Implementation

### API Endpoint

```http
DELETE /api/v1/bots/{bot_id}?liquidate={boolean}
```

**Parameters**:
- `bot_id` (path): Bot ID to delete
- `liquidate` (query, optional): `true` to liquidate holdings, `false` to delete only (default: `false`)

**Response**:
```json
{
  "message": "Bot deleted successfully",
  "liquidation": {
    "product_id": "XLM-USD",
    "holdings_liquidated": 123.45,
    "trade_executed": true,
    "order_id": "abc-123-def",
    "error": null
  }
}
```

### Backend Logic Flow

```python
# 1. Validate bot exists
bot = db.query(Bot).filter(Bot.id == bot_id).first()

# 2. If liquidate=true, sell holdings
if liquidate:
    - Get Coinbase account balance for base currency
    - If holdings > 0:
        * Place market SELL order
        * Record order_id in response
        * Background Celery task will sync trade later
    - If holdings == 0:
        * Skip trade execution
        * Return holdings_liquidated: 0

# 3. Delete all child records (CRITICAL ORDER)
db.query(Trade).filter(Trade.bot_id == bot_id).delete()
db.query(BotSignalHistory).filter(BotSignalHistory.bot_id == bot_id).delete()
db.query(AdaptiveSignalWeights).filter(AdaptiveSignalWeights.bot_id == bot_id).delete()
db.query(SignalPredictionRecord).filter(SignalPredictionRecord.pair == bot.pair).delete()

# 4. Flush deletions to satisfy foreign key constraints
db.flush()

# 5. Delete the bot
db.delete(bot)
db.commit()
```

### Critical Design Decisions

#### 1. **db.flush() Required**
SQLite enforces foreign key constraints immediately during transaction. Without `db.flush()` after deleting child records, the `db.delete(bot)` call fails with:
```
FOREIGN KEY constraint failed
```

The flush commits child deletions to the transaction BEFORE attempting parent deletion.

#### 2. **No Immediate Sync**
Original implementation called `raw_trade_service.sync_trades_for_product()` immediately after liquidation, causing:
- ❌ 30+ second hangs waiting for Coinbase API
- ❌ Frontend timeout errors
- ❌ Modal staying open indefinitely
- ❌ Bot not disappearing from UI

**Solution**: Remove immediate sync. Celery background task will sync trades automatically within minutes.

#### 3. **Complete Cascade Deletion**
All related records are deleted to prevent orphaned data:
- `Trade` - Historical trades by this bot
- `BotSignalHistory` - Signal scoring history
- `AdaptiveSignalWeights` - Learning system weights
- `SignalPredictionRecord` - Prediction records for the pair

This is **Option A: Clean Slate** - delete ALL history for a fresh start.

#### 4. **Optimistic UI Updates**
Frontend uses React Query's `onMutate` to immediately remove bot from UI before API response returns, providing instant feedback.

---

## Frontend Implementation

### Hook: `useDeleteBot()`

```typescript
// frontend/src/hooks/useBots.ts
export const useDeleteBot = () => {
  const queryClient = useQueryClient();
  
  return useMutation({
    mutationFn: async ({ botId, liquidate }: { botId: number; liquidate: boolean }) => {
      const response = await api.delete(`/bots/${botId}?liquidate=${liquidate}`);
      return response.data;
    },
    onMutate: async ({ botId }) => {
      // Optimistic update: remove bot immediately
      await queryClient.cancelQueries({ queryKey: ['bots'] });
      const previousBots = queryClient.getQueryData(['bots']);
      
      queryClient.setQueryData(['bots'], (old: Bot[] | undefined) => {
        return old ? old.filter(bot => bot.id !== botId) : [];
      });
      
      return { previousBots };
    },
    onError: (_err, _vars, context) => {
      // Rollback on error
      if (context?.previousBots) {
        queryClient.setQueryData(['bots'], context.previousBots);
      }
    },
    onSuccess: () => {
      // Invalidate cache to refetch
      queryClient.invalidateQueries({ queryKey: ['bots'] });
      queryClient.invalidateQueries({ queryKey: ['bots', 'status'] });
    },
  });
};
```

### Component: `DeleteBotModal`

```typescript
// frontend/src/components/Dashboard/DeleteBotModal.tsx
const [liquidate, setLiquidate] = useState(true); // Default to true

// Checkbox in modal
<input
  type="checkbox"
  checked={liquidate}
  onChange={(e) => setLiquidate(e.target.checked)}
/>

// Confirm button
<button onClick={() => onConfirm(liquidate)}>
  {liquidate ? 'Liquidate & Delete' : 'Delete Bot'}
</button>
```

### Integration: Bot Display Components

All three bot display components integrate the modal:
- `TieredBotsView.tsx`
- `DualViewBotsDisplay.tsx`
- `Signals.tsx`

```typescript
const [deletingBot, setDeletingBot] = useState<{id: number; name: string} | null>(null);
const deleteBot = useDeleteBot();

// Delete button click
<button onClick={() => setDeletingBot({id: bot.id, name: bot.name})}>
  Delete
</button>

// Modal
<DeleteBotModal
  isOpen={deletingBot !== null}
  botName={deletingBot?.name || ''}
  onCancel={() => setDeletingBot(null)}
  onConfirm={(liquidate) => {
    if (deletingBot) {
      deleteBot.mutate(
        { botId: deletingBot.id, liquidate },
        {
          onSuccess: () => {
            toast.success(`Bot "${deletingBot.name}" deleted`);
            setDeletingBot(null);
          },
          onError: () => {
            toast.error(`Failed to delete bot`);
            setDeletingBot(null);
          }
        }
      );
    }
  }}
/>
```

---

## Critical Bug Fixes Applied

### 1. **BotResponse Schema Mismatch** (October 9, 2025)
**Problem**: `create_bot()` returned raw `Bot` object, but `BotResponse` schema required computed field `trading_thresholds`.

**Symptom**: Bot creation returned HTTP 500 "Internal Server Error" but bot was actually created in database.

**Fix**: Use `prepare_bot_response(bot)` in both `create_bot()` and `update_bot()` to add computed fields.

```python
# Before
return db_bot

# After
return prepare_bot_response(db_bot)
```

### 2. **Order Result Check** (October 9, 2025)
**Problem**: Checked `order_result.get('success')` but Coinbase service returns `{'order_id': '...', 'status': 'pending'}`.

**Symptom**: Liquidation trade executed on Coinbase but reported as failed in response.

**Fix**: Check `order_result.get('order_id')` instead.

```python
# Before
if order_result and order_result.get('success'):

# After  
if order_result and order_result.get('order_id'):
```

### 3. **Missing Foreign Key Deletions** (October 9, 2025)
**Problem**: Only deleted `Trade` and `SignalPredictionRecord`, missed `BotSignalHistory` and `AdaptiveSignalWeights`.

**Symptom**: `FOREIGN KEY constraint failed` on bot deletion.

**Fix**: Delete ALL child tables with `bot_id` foreign key.

```python
db.query(Trade).filter(Trade.bot_id == bot_id).delete()
db.query(BotSignalHistory).filter(BotSignalHistory.bot_id == bot_id).delete()
db.query(AdaptiveSignalWeights).filter(AdaptiveSignalWeights.bot_id == bot_id).delete()
db.query(SignalPredictionRecord).filter(SignalPredictionRecord.pair == bot.pair).delete()
```

### 4. **Transaction Flush Required** (October 9, 2025)
**Problem**: SQLite checks foreign keys immediately. Without flushing child deletions, bot deletion fails.

**Symptom**: `FOREIGN KEY constraint failed` even after adding all child deletions.

**Fix**: Add `db.flush()` after child deletions, before bot deletion.

```python
# Delete children
db.query(Trade).filter(...).delete()
# ... more deletions ...

# CRITICAL: Flush to database
db.flush()

# Now safe to delete parent
db.delete(bot)
db.commit()
```

### 5. **Hanging Sync Call** (October 9, 2025)
**Problem**: `raw_trade_service.sync_trades_for_product()` called immediately after liquidation, causing 30+ second hangs.

**Symptom**: 
- Frontend API call never returns
- Modal stays open
- Bot remains in UI
- Trade appears in Coinbase but frontend shows nothing

**Fix**: Remove immediate sync. Celery background task handles sync automatically.

```python
# Before
time.sleep(2)
raw_trade_service.sync_trades_for_product(product_id)

# After
# Note: Sync will happen automatically via scheduled Celery task
# No need to sync immediately - avoid blocking the delete request
```

---

## Testing

### Manual Test Cases

#### Test 1: Delete with Liquidation (Holdings Exist)
```bash
# Create test bot
curl -X POST "http://localhost:8000/api/v1/bots/" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "TEST-BOT",
    "description": "Test deletion",
    "pair": "DOGE-USD",
    "is_active": true,
    "signal_config": {...}
  }'

# Delete with liquidation
curl -X DELETE "http://localhost:8000/api/v1/bots/54?liquidate=true"

# Expected response:
{
  "message": "Bot deleted successfully",
  "liquidation": {
    "product_id": "DOGE-USD",
    "holdings_liquidated": 10.5,
    "trade_executed": true,
    "order_id": "abc-123",
    "error": null
  }
}

# Verify:
# 1. Bot deleted from database
# 2. Trade appears in Coinbase
# 3. Bot count decreased by 1
```

#### Test 2: Delete with Liquidation (No Holdings)
```bash
curl -X DELETE "http://localhost:8000/api/v1/bots/54?liquidate=true"

# Expected:
{
  "message": "Bot deleted successfully",
  "liquidation": {
    "product_id": "DOGE-USD",
    "holdings_liquidated": 0,
    "trade_executed": false,
    "error": null
  }
}
```

#### Test 3: Delete Without Liquidation
```bash
curl -X DELETE "http://localhost:8000/api/v1/bots/54?liquidate=false"

# Expected:
{
  "message": "Bot deleted successfully"
}
```

#### Test 4: UI Integration
1. Open dashboard at http://localhost:3000
2. Click delete button on any bot
3. Verify modal appears with checkbox checked
4. Click "Liquidate & Delete"
5. Verify:
   - Modal closes immediately
   - Bot disappears from list
   - Toast notification appears
   - Trade appears in Coinbase (if holdings existed)

### Automated Tests
*TODO: Add pytest tests for bot deletion endpoint*

---

## Database Schema

### Tables with Foreign Keys to `bots`

```sql
-- Deleted automatically on bot deletion:
CREATE TABLE trades (
    id INTEGER PRIMARY KEY,
    bot_id INTEGER REFERENCES bots(id)  -- FK constraint
);

CREATE TABLE bot_signal_history (
    id INTEGER PRIMARY KEY,
    bot_id INTEGER REFERENCES bots(id)  -- FK constraint
);

CREATE TABLE adaptive_signal_weights (
    id INTEGER PRIMARY KEY,
    bot_id INTEGER REFERENCES bots(id)  -- FK constraint
);

CREATE TABLE signal_prediction_records (
    id INTEGER PRIMARY KEY,
    pair TEXT  -- Matched to bot.pair, not bot_id
);
```

---

## Known Limitations

1. **No Undo**: Once deleted, bot and all history are permanently removed
2. **No Partial Liquidation**: All holdings are sold at market price
3. **Market Orders Only**: Uses market orders which may have slippage
4. **No Confirmation of Trade Fill**: Returns immediately, doesn't wait for Coinbase fill confirmation
5. **Celery Required**: Trade sync depends on Celery beat scheduler running

---

## Future Improvements

1. **Soft Delete**: Add `deleted_at` timestamp instead of hard delete to preserve history
2. **Limit Orders**: Option to use limit orders for better pricing
3. **Partial Liquidation**: Allow specifying percentage to liquidate
4. **Trade Confirmation**: Wait for Coinbase fill confirmation before responding
5. **Undo Window**: 30-second grace period to cancel deletion
6. **Audit Log**: Track who deleted what and when
7. **Bulk Delete**: Select multiple bots to delete at once

---

## Related Files

### Backend
- `/backend/app/api/bots.py` - Delete endpoint (lines 201-330)
- `/backend/app/models/models.py` - Database models with foreign keys
- `/backend/app/services/coinbase_service.py` - `place_market_order()` function
- `/backend/app/services/raw_trade_service.py` - Trade sync service

### Frontend
- `/frontend/src/hooks/useBots.ts` - `useDeleteBot()` hook
- `/frontend/src/components/Dashboard/DeleteBotModal.tsx` - Confirmation modal
- `/frontend/src/components/Dashboard/TieredBotsView.tsx` - Bot display integration
- `/frontend/src/components/Dashboard/DualViewBotsDisplay.tsx` - Alternative view integration
- `/frontend/src/pages/Signals.tsx` - Signals page integration

---

## Change Log

### October 9, 2025
- ✅ Initial implementation of liquidation feature
- ✅ Fixed `BotResponse` schema mismatch in create/update endpoints
- ✅ Fixed order result checking (success → order_id)
- ✅ Added missing foreign key deletions (BotSignalHistory, AdaptiveSignalWeights)
- ✅ Added `db.flush()` to satisfy foreign key constraints
- ✅ Removed blocking sync call that caused 30s+ hangs
- ✅ Tested end-to-end: liquidation executes, modal closes, bot disappears
- ✅ Documentation created

---

## Support

**Issues?** Check:
1. Backend logs: `/Users/lazy_genius/Projects/trader/logs/backend.log`
2. Browser console for frontend errors
3. Coinbase account to verify trades executed
4. Database: `sqlite3 /Users/lazy_genius/Projects/trader/trader.db "SELECT * FROM bots;"`

**Common Errors**:
- "Bot not found" → Bot ID doesn't exist
- "FOREIGN KEY constraint failed" → Missing `db.flush()` or child deletion
- Modal doesn't close → Check browser console for API errors
- Trade not executing → Check Coinbase API credentials and account balance
