# P&L Calculation Fix Implementation Plan

## Root Cause
The current P&L calculation treats "money spent on open positions" as "realized losses", which is fundamentally incorrect in financial accounting.

## Current (Wrong) Logic
```python
realized_pnl = total_received - total_spent
```
For AVNT bot:
- total_received = $0 (no sells)
- total_spent = $282.18
- realized_pnl = -$282.18 (WRONG - this is not a loss!)

## Correct Logic
```python
# Realized P&L = profit/loss from completed trade cycles only
realized_pnl = 0.0
for each sell_trade:
    # Match with FIFO buy trades
    proceeds = sell_trade.value
    cost = sum(matched_buy_trades.value)
    realized_pnl += (proceeds - cost)

# Unrealized P&L = current value vs cost basis of remaining position
unrealized_pnl = current_position_value - cost_basis_of_remaining_coins
```

## Implementation Steps

### 1. Fix Bot Performance Endpoint
File: `backend/app/api/trades.py` - Line 258

**Before:**
```python
realized_pnl = total_received - total_spent  # WRONG
```

**After:**
```python
realized_pnl = calculate_realized_pnl_fifo(trades)  # Use FIFO matching
```

### 2. Create FIFO P&L Calculator
File: `backend/app/utils/pnl_calculator.py` (new file)

```python
def calculate_realized_pnl_fifo(trades):
    """Calculate realized P&L using FIFO matching of buy/sell orders"""
    buy_queue = []  # FIFO queue of buy orders
    realized_pnl = 0.0
    
    for trade in sorted(trades, key=lambda t: t.created_at):
        if trade.side.upper() == 'BUY':
            buy_queue.append({
                'size': trade.size,
                'price': trade.price,
                'value': get_trade_usd_value(trade)
            })
        elif trade.side.upper() == 'SELL':
            sell_size = trade.size
            sell_value = get_trade_usd_value(trade)
            sell_price = trade.price
            
            # Match against buy orders (FIFO)
            while sell_size > 0 and buy_queue:
                buy_order = buy_queue[0]
                
                if buy_order['size'] <= sell_size:
                    # Sell entire buy order
                    proceeds = buy_order['size'] * sell_price
                    cost = buy_order['value']
                    realized_pnl += (proceeds - cost)
                    
                    sell_size -= buy_order['size']
                    buy_queue.pop(0)
                else:
                    # Partial sell
                    proceeds = sell_size * sell_price
                    cost = sell_size * buy_order['price']
                    realized_pnl += (proceeds - cost)
                    
                    buy_order['size'] -= sell_size
                    buy_order['value'] -= cost
                    sell_size = 0
    
    return realized_pnl
```

### 3. Update All Affected Endpoints
- `/api/v1/trades/bot/{bot_id}/performance`
- `/api/v1/trades/analytics/live-performance`
- `/api/v1/trades/product/{product}/pnl`
- Raw trade service statistics

### 4. Fix Frontend Components
Update bot cards to show:
- Realized P&L: $0.00 (for open positions like AVNT)
- Unrealized P&L: $274.25 - $282.18 = -$7.93
- Total P&L: -$7.93 (not -$287.56!)

## Impact Analysis

### Before Fix (Current State)
- AVNT shows -$287.56 loss (fake)
- BONK shows -$64.80 loss (fake)
- Dashboard hiding reality of small actual losses

### After Fix (Correct State)
- AVNT shows -$7.93 loss (real unrealized loss)
- BONK shows actual small unrealized loss
- Dashboard shows true financial position

## Verification Plan
1. Test with AVNT bot (only buys): realized P&L = $0.00
2. Test with BTC bot (buys + sells): realized P&L = actual profit/loss
3. Verify total portfolio P&L matches Coinbase balance changes
4. Confirm UI shows correct values

## Timeline
- Immediate: Fix core calculation logic
- Short-term: Update all endpoints
- Medium-term: Add comprehensive P&L tests
- Long-term: Add P&L audit trail

This fix will restore accurate financial reporting to the trading system.
