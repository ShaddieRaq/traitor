# Phase 9: Portfolio Management System - Implementation Plan

**Date**: October 11, 2025  
**Status**: Planning → Implementation  
**Goal**: Build intelligent portfolio manager that prevents losses like yesterday's market crash

---

## 🎯 Current Situation

### What We Have Now (October 11, 2025)
1. ✅ **Bot.stop_loss_pct** and **Bot.take_profit_pct** fields in database (default 5% and 10%)
2. ✅ **Profit protection methods** in `bot_evaluator.py`:
   - `calculate_position_pnl_percent()` - Calculates P&L from RawTrade history
   - `should_sell_for_profit_protection()` - Checks take profit/stop loss
   - `has_existing_position()` - Prevents double buys
3. ⚠️ **Issue**: Code detects profit protection but doesn't execute trades (missing integration)
4. 📊 **Current Portfolio**: 27 positions, 20 need stop-loss protection (-12% to -45% losses)

### What Happened Yesterday (October 10, 2025)
- Market crash wiped out all unrealized gains
- Bots held positions indefinitely waiting for signal reversals
- No automatic profit-taking or loss-cutting
- User lost confidence in AI system's ability to protect capital

---

## 🏗️ Architecture: Portfolio Management System

### Core Components to Build

```
PortfolioManager
├── PositionMonitor - Track all open positions
├── RiskController - Stop loss + take profit execution
├── ScalingEngine - Dynamic position sizing (1x → 3x winners, 1x → 0.2x losers)
├── CapitalAllocator - Move capital from losers to winners
└── PortfolioAnalytics - Real-time P&L, heat maps, correlation
```

### Integration Points
1. **Celery Task**: `portfolio_management_task()` runs every 5 minutes
2. **Bot Evaluator**: Consults portfolio manager before placing trades
3. **Trading Service**: Executes portfolio manager decisions
4. **API Endpoints**: `/api/v1/portfolio/*` for monitoring

---

## 📋 Implementation Phases

### Phase 9.1: Risk Controller (Week 1) - **URGENT**
**Goal**: Activate stop-loss and take-profit to prevent future crashes

**Tasks**:
1. ✅ Create `PortfolioRiskController` class
2. ✅ Integrate with `fast_trading_evaluation` Celery task
3. ✅ Execute automatic sells when stop-loss/take-profit hit
4. ✅ Test with current 20 positions needing protection
5. ✅ Monitor first 24 hours of automatic protection

**Deliverable**: Working stop-loss system that would have prevented yesterday's losses

---

### Phase 9.2: Position Scaling (Week 2)
**Goal**: Scale winners up, scale losers down

**Tasks**:
1. Create `PositionScalingEngine` class
2. Implement scaling tiers:
   - +$10 profit → 1.25x position
   - +$25 profit → 1.5x position
   - +$40 profit → 2x position
   - -$10 loss → 0.75x position
   - -$20 loss → 0.5x position
3. Add `position_multiplier` field to Bot model
4. Test scaling with current winners (TOSHI, DASH)

**Deliverable**: Dynamic position sizing based on performance

---

### Phase 9.3: Capital Reallocation (Week 3)
**Goal**: Move capital from losing strategies to winning strategies

**Tasks**:
1. Create `CapitalAllocator` class
2. Implement reallocation logic:
   - Scale down losers → Free up capital
   - Identify winners with momentum → Allocate freed capital
3. Add portfolio-level capital limits (max 30% in any single position)
4. Test capital movement between positions

**Deliverable**: Automatic capital flow optimization

---

### Phase 9.4: Portfolio Analytics (Week 4)
**Goal**: Real-time visibility into portfolio health

**Tasks**:
1. Create `PortfolioAnalytics` service
2. Build analytics dashboard:
   - Total P&L by position
   - Correlation heatmap
   - Risk concentration metrics
   - Sharpe ratio by bot
3. Add `/api/v1/portfolio/analytics` endpoint
4. Create React dashboard component

**Deliverable**: Portfolio management UI

---

## 🚀 Quick Start: Phase 9.1 Implementation

### Step 1: Create Portfolio Risk Controller

**File**: `/backend/app/services/portfolio_risk_controller.py`

```python
from typing import Dict, List, Optional, Tuple
from sqlalchemy.orm import Session
from ..models.models import Bot
from .bot_evaluator import BotSignalEvaluator
from .sync_trading_service import get_trading_service
import logging

logger = logging.getLogger(__name__)

class PortfolioRiskController:
    """
    Manages portfolio-level risk controls including stop-loss and take-profit.
    
    This is the risk management layer that sits above individual bot strategies,
    ensuring capital protection even when signal-based trading would wait.
    """
    
    def __init__(self, db: Session):
        self.db = db
        self.evaluator = BotSignalEvaluator(db, enable_confirmation=False)
        self.trading_service = get_trading_service()
    
    def scan_and_protect_portfolio(self) -> Dict[str, any]:
        """
        Scan all active positions and execute profit protection trades.
        
        Returns:
            Dict with execution results
        """
        results = {
            'scanned': 0,
            'stop_loss_executed': 0,
            'take_profit_executed': 0,
            'errors': [],
            'trades': []
        }
        
        # Get all running bots
        active_bots = self.db.query(Bot).filter(Bot.status == 'RUNNING').all()
        
        for bot in active_bots:
            try:
                results['scanned'] += 1
                
                # Check if bot has position
                if not self.evaluator.has_existing_position(bot):
                    continue
                
                # Calculate P&L
                pnl_percent = self.evaluator.calculate_position_pnl_percent(bot)
                if pnl_percent is None:
                    continue
                
                # Check profit protection
                should_sell, reason = self.evaluator.should_sell_for_profit_protection(bot, pnl_percent)
                
                if should_sell:
                    # Execute protective sell
                    trade_result = self._execute_protective_sell(bot, reason, pnl_percent)
                    
                    if trade_result.get('success'):
                        if 'STOP_LOSS' in reason:
                            results['stop_loss_executed'] += 1
                        elif 'TAKE_PROFIT' in reason:
                            results['take_profit_executed'] += 1
                        
                        results['trades'].append({
                            'bot_id': bot.id,
                            'pair': bot.pair,
                            'reason': reason,
                            'pnl_percent': pnl_percent,
                            'order_id': trade_result.get('order_id')
                        })
                        
                        logger.info(f"✅ Portfolio protection: {reason} for {bot.pair}")
                    else:
                        results['errors'].append({
                            'bot_id': bot.id,
                            'pair': bot.pair,
                            'error': trade_result.get('error')
                        })
                        logger.error(f"❌ Failed portfolio protection for {bot.pair}: {trade_result.get('error')}")
                        
            except Exception as e:
                logger.error(f"Error scanning bot {bot.id}: {e}")
                results['errors'].append({
                    'bot_id': bot.id,
                    'pair': bot.pair,
                    'error': str(e)
                })
        
        return results
    
    def _execute_protective_sell(self, bot: Bot, reason: str, pnl_percent: float) -> Dict[str, any]:
        """
        Execute a protective sell order (stop-loss or take-profit).
        """
        try:
            # Get current holdings
            from .sync_coordinated_coinbase_service import get_coordinated_coinbase_service
            coinbase = get_coordinated_coinbase_service()
            
            accounts = coinbase.get_accounts()
            base_currency = bot.pair.split('-')[0]
            
            holding = None
            for account in accounts:
                if account['currency'] == base_currency:
                    holding = float(account['available_balance'])
                    break
            
            if not holding or holding <= 0:
                return {'success': False, 'error': 'No holdings to sell'}
            
            # Execute market sell
            order = coinbase.place_market_order(
                product_id=bot.pair,
                side='sell',
                size=holding
            )
            
            if order and order.get('order_id'):
                # Update bot with trade reason
                bot.last_trade_reason = reason
                self.db.commit()
                
                logger.info(f"🛡️ PORTFOLIO PROTECTION: Sold {holding} {base_currency} - {reason}")
                
                return {
                    'success': True,
                    'order_id': order['order_id'],
                    'size': holding,
                    'reason': reason
                }
            else:
                return {'success': False, 'error': 'Order placement failed'}
                
        except Exception as e:
            logger.error(f"Error executing protective sell: {e}")
            return {'success': False, 'error': str(e)}

# Singleton pattern
_portfolio_risk_controller = None

def get_portfolio_risk_controller(db: Session) -> PortfolioRiskController:
    """Get or create portfolio risk controller instance."""
    return PortfolioRiskController(db)
```

### Step 2: Create Celery Task

**File**: `/backend/app/tasks/portfolio_tasks.py`

```python
from celery import Task
from ..core.database import SessionLocal
from ..services.portfolio_risk_controller import get_portfolio_risk_controller
from .celery_app import celery_app
import logging

logger = logging.getLogger(__name__)

@celery_app.task(name="app.tasks.portfolio_tasks.portfolio_protection_scan")
def portfolio_protection_scan():
    """
    Scan portfolio for stop-loss and take-profit conditions.
    Executes protective trades independent of signal-based trading.
    
    Runs every 5 minutes to ensure capital protection.
    """
    logger.info("🛡️ Starting portfolio protection scan...")
    
    db = SessionLocal()
    try:
        controller = get_portfolio_risk_controller(db)
        results = controller.scan_and_protect_portfolio()
        
        logger.info(f"🛡️ Portfolio scan complete: {results}")
        
        return {
            'status': 'success',
            'scanned_bots': results['scanned'],
            'stop_loss_trades': results['stop_loss_executed'],
            'take_profit_trades': results['take_profit_executed'],
            'errors': len(results['errors']),
            'trades': results['trades']
        }
        
    except Exception as e:
        logger.error(f"Error in portfolio protection scan: {e}")
        return {
            'status': 'error',
            'message': str(e)
        }
    finally:
        db.close()
```

### Step 3: Schedule Celery Task

**File**: `/backend/app/tasks/celery_app.py` (add to beat_schedule)

```python
beat_schedule={
    # ... existing tasks ...
    
    # PHASE 9.1: Portfolio Risk Controller
    "portfolio-protection-scan": {
        "task": "app.tasks.portfolio_tasks.portfolio_protection_scan",
        "schedule": 300.0,  # Every 5 minutes - capital protection
    },
}
```

### Step 4: Add Portfolio Tasks to Celery Includes

```python
celery_app = Celery(
    "trading_bot",
    broker=settings.redis_url,
    backend=settings.redis_url,
    include=[
        "app.tasks.trading_tasks", 
        "app.tasks.data_tasks", 
        "app.tasks.market_analysis_tasks", 
        "app.tasks.new_pair_tasks",
        "app.tasks.market_data_tasks",
        "app.tasks.portfolio_tasks"  # NEW
    ]
)
```

---

## 🧪 Testing Plan

### Test 1: Verify Stop-Loss Detection
```bash
# Check current positions needing protection
python -c "
from backend.app.core.database import SessionLocal
from backend.app.services.portfolio_risk_controller import get_portfolio_risk_controller

db = SessionLocal()
controller = get_portfolio_risk_controller(db)
results = controller.scan_and_protect_portfolio()
print(f'Stop losses needed: {results[\"stop_loss_executed\"]}')
db.close()
"
```

### Test 2: Monitor First Execution
```bash
# Watch for portfolio protection in logs
tail -f logs/celery-worker.log | grep "portfolio_protection_scan"
```

### Test 3: Verify Trade Execution
```bash
# Check if actual trades executed
curl -s "http://localhost:8000/api/v1/raw-trades/recent" | jq '.[] | select(.side == "sell")'
```

---

## 📈 Success Metrics

**Phase 9.1 Success = Capital Protection Active**
- [ ] Portfolio scan runs every 5 minutes
- [ ] Stop-loss trades execute automatically when positions hit -5%
- [ ] Take-profit trades execute automatically when positions hit +10%
- [ ] Zero system errors during execution
- [ ] User sees capital protected in real-time

**Current Portfolio Test Case**:
- 20 positions currently at -12% to -45% losses
- All should sell automatically on first scan
- Expected: $100+ in loss prevention (if crash continues)

---

## 🎯 Next Steps (Priority Order)

1. **Create** `portfolio_risk_controller.py` ← **START HERE**
2. **Create** `portfolio_tasks.py`
3. **Update** `celery_app.py` to include portfolio tasks and schedule
4. **Restart** services to activate portfolio protection
5. **Monitor** first 24 hours of automatic protection
6. **Document** results and move to Phase 9.2

---

## 💡 Key Architectural Decisions

### Why Separate Portfolio Manager?
- **Bot Evaluator**: Signal-based trading logic (RSI, MA, MACD)
- **Portfolio Manager**: Capital protection logic (stop-loss, take-profit, scaling)
- **Separation of Concerns**: Trading strategy ≠ Risk management

### Why Celery Task Instead of Bot Evaluator?
- **Independent Execution**: Runs even if signal evaluation is slow
- **Portfolio-Level View**: Sees all positions, not individual bots
- **Capital Protection Priority**: Executes before signal-based trades

### Why 5-Minute Interval?
- **Balance**: Frequent enough to catch moves, not so frequent to spam API
- **Faster than Signal Evaluation**: 10-minute bot evaluation + 5-minute protection = layered defense
- **User Confidence**: User sees system actively protecting capital

---

**Ready to implement Phase 9.1?** Start with creating `portfolio_risk_controller.py`!
