# Phase 9: Portfolio Management System - Clean Implementation Roadmap
**Date**: October 11, 2025  
**Status**: Ready for Implementation

## Executive Summary

**What to Remove**: Emergency profit protection code (Phase 9A) - incomplete and architecturally wrong  
**What to Build**: Full Portfolio Management System (Phase 9) - proper architecture with learning + scaling hybrid

---

## PART 1: Code Cleanup (30 minutes)

### Files to Modify

#### 1. `/backend/app/services/bot_evaluator.py`

**Remove these sections:**
```python
# Lines 58-106: REMOVE - Emergency profit protection override in evaluate_bot()
# This code breaks proper signal evaluation flow
```

**Keep but prepare to migrate:**
```python
# Lines 1433-1523: calculate_position_pnl_percent() - MOVE to portfolio_manager.py
# Lines 1524-1560: should_sell_for_profit_protection() - DELETE (replaced by HybridDecisionEngine)
# Lines 1562-1590: has_existing_position() - MOVE to portfolio_manager.py
```

**Keep as-is:**
```python
# Lines 498-507: Profit protection hook in _determine_action() - Portfolio Manager will use this
# Lines 570-583: Position check utility - useful for multiple services
```

#### 2. `/backend/app/models/models.py`

**Keep:**
```python
# Lines 22-23: stop_loss_pct, take_profit_pct - Part of bot configuration
```

**Remove:**
```python
# Line 45: last_trade_reason - Portfolio Manager will use PortfolioAction table instead
```

#### 3. Documentation Cleanup

**Archive (move to `/docs/archived/`):**
- `PHASE_9A_EMERGENCY_PROFIT_PROTECTION.md`
- `PHASE_9A_IMPLEMENTATION_LOG.md`

**Update:**
- `ROADMAP_STATUS_OCTOBER_2025.md` - Reflect proper Phase 9 approach

---

## PART 2: Portfolio Management System Architecture

### New Files to Create

#### 1. `/backend/app/services/portfolio_manager.py` (Core Service)

**Classes to implement:**

```python
from dataclasses import dataclass
from typing import Dict, Any, List, Optional
from backend.app.services.adaptive_weighting_service import get_adaptive_weighting_service
from backend.app.services.market_data_service import get_market_data_service

@dataclass
class HybridPortfolioSettings:
    """Configurable portfolio management parameters"""
    # Learning System Triggers
    learning_activation_loss: float = -5.0      # Start learning at -$5 loss
    parameter_adjustment_period: int = 14       # Days to evaluate changes
    min_predictions_for_learning: int = 10      # Min data for parameter changes
    
    # Position Scaling Triggers  
    immediate_scale_down_loss: float = -10.0    # Scale down at -$10 loss
    emergency_liquidation_loss: float = -40.0   # Liquidate at -$40 loss
    momentum_scale_up_profit: float = 15.0      # Scale up at +$15 profit
    
    # Risk Management
    max_position_reduction: float = 0.8         # Max 80% position reduction
    max_position_increase: float = 3.0          # Max 3x position scaling
    volatility_scaling_factor: bool = True      # Adjust for volatility


class HybridPortfolioDecisionEngine:
    """
    Combines learning system optimization with position scaling.
    Makes intelligent decisions about when to learn vs when to scale.
    """
    
    def __init__(self, settings: Optional[HybridPortfolioSettings] = None):
        self.settings = settings or HybridPortfolioSettings()
        self.learning_service = get_adaptive_weighting_service()
        self.position_service = PositionScalingService(self.settings)
    
    def evaluate_bot_action(self, bot: Bot, performance_data: Dict) -> Dict[str, Any]:
        """
        Determine optimal action: learn, scale_down, scale_up, liquidate, or hold.
        
        Args:
            bot: Bot instance
            performance_data: {
                'total_pnl_usd': float,
                'confidence': float,
                'days_since_profit': int,
                'volatility_pct': float,
                'current_position_size': float
            }
        
        Returns:
            {
                'action': 'learn' | 'scale_down' | 'scale_up' | 'liquidate' | 'hold',
                'learning_changes': {...} or None,
                'position_changes': {...} or None,
                'rationale': str
            }
        """
        current_pnl = performance_data.get('total_pnl_usd', 0)
        confidence = performance_data.get('confidence', 0)
        days_since_profit = performance_data.get('days_since_profit', 0)
        
        # PRIORITY 1: Emergency liquidation
        if current_pnl <= self.settings.emergency_liquidation_loss:
            return {
                'action': 'liquidate',
                'learning_changes': None,
                'position_changes': {'new_multiplier': 0, 'reason': 'emergency_stop'},
                'rationale': f'Emergency stop: Loss ${current_pnl} exceeds ${self.settings.emergency_liquidation_loss} threshold'
            }
        
        # PRIORITY 2: Momentum scaling (winners)
        if current_pnl >= self.settings.momentum_scale_up_profit:
            scaling_action = self.position_service.calculate_momentum_scaling(bot, performance_data)
            learning_action = self.learning_service.process_bot_weight_update(bot.id)
            return {
                'action': 'scale_up',
                'position_changes': scaling_action,
                'learning_changes': learning_action,
                'rationale': f'Momentum detected: ${current_pnl} profit, scaling position and optimizing signals'
            }
        
        # PRIORITY 3: Risk management (moderate losers)
        if self.settings.immediate_scale_down_loss <= current_pnl < 0:
            # Determine: scale vs learn priority based on recency
            if days_since_profit < 7:
                # Recent activity - parameter issue, focus on learning
                return {
                    'action': 'learn',
                    'learning_changes': self.learning_service.process_bot_weight_update(bot.id),
                    'position_changes': {'new_multiplier': 0.8, 'reason': 'minor_scale_during_learning'},
                    'rationale': f'Recent losses ${current_pnl}, prioritizing parameter adjustment with minor position reduction'
                }
            else:
                # Extended losses - risk management priority
                return {
                    'action': 'scale_down',
                    'position_changes': self.position_service.calculate_risk_scaling(bot, performance_data),
                    'learning_changes': self.learning_service.process_bot_weight_update(bot.id),
                    'rationale': f'Extended losses ${current_pnl}, prioritizing risk reduction while learning adapts'
                }
        
        # PRIORITY 4: Stable performance (maintain + learn)
        return {
            'action': 'hold',
            'learning_changes': self.learning_service.process_bot_weight_update(bot.id),
            'position_changes': None,
            'rationale': f'Stable performance ${current_pnl}, maintaining position while optimizing signals'
        }


class PositionScalingService:
    """Handles dynamic position size calculations"""
    
    def __init__(self, settings: HybridPortfolioSettings):
        self.settings = settings
    
    def calculate_momentum_scaling(self, bot: Bot, performance_data: Dict) -> Dict[str, Any]:
        """Calculate position scaling for profitable momentum"""
        current_pnl = performance_data.get('total_pnl_usd', 0)
        volatility = performance_data.get('volatility_pct', 100)
        
        # Base scaling tiers (profit-based)
        if current_pnl >= 40:
            base_scale = 2.0      # 2x position at +$40
        elif current_pnl >= 25:
            base_scale = 1.5      # 1.5x position at +$25
        elif current_pnl >= 15:
            base_scale = 1.25     # 1.25x position at +$15
        else:
            base_scale = 1.0      # No scaling
        
        # Volatility adjustment
        if self.settings.volatility_scaling_factor:
            if volatility > 200:
                vol_adjustment = 0.7   # Reduce for high volatility
            elif volatility < 50:
                vol_adjustment = 1.2   # Boost for low volatility
            else:
                vol_adjustment = 1.0
            adjusted_scale = base_scale * vol_adjustment
        else:
            adjusted_scale = base_scale
        
        # Apply maximum limit
        final_scale = min(adjusted_scale, self.settings.max_position_increase)
        
        return {
            'new_multiplier': final_scale,
            'base_scale': base_scale,
            'volatility_adjustment': adjusted_scale / base_scale if base_scale > 0 else 1.0,
            'reason': f'Momentum scaling for ${current_pnl} profit, {volatility}% volatility'
        }
    
    def calculate_risk_scaling(self, bot: Bot, performance_data: Dict) -> Dict[str, Any]:
        """Calculate position scaling for risk management (losers)"""
        current_pnl = performance_data.get('total_pnl_usd', 0)
        confidence = performance_data.get('confidence', 0)
        
        # Risk-based scaling (loss severity)
        if current_pnl <= -20:
            risk_scale = 0.3      # 70% reduction at -$20
        elif current_pnl <= -10:
            risk_scale = 0.5      # 50% reduction at -$10
        elif confidence < 0.2:
            risk_scale = 0.6      # 40% reduction for low confidence
        else:
            risk_scale = 0.8      # 20% reduction
        
        # Apply minimum position limit (can't reduce more than max_position_reduction)
        final_scale = max(risk_scale, 1 - self.settings.max_position_reduction)
        
        return {
            'new_multiplier': final_scale,
            'reason': f'Risk scaling for ${current_pnl} loss, {confidence:.1%} confidence'
        }
    
    def calculate_position_pnl_percent(self, bot: Bot, db: Session) -> float:
        """
        Calculate current position P&L percentage.
        Migrated from bot_evaluator.py emergency code.
        """
        from backend.app.services.raw_trade_service import RawTradeService
        
        raw_trade_service = RawTradeService(db)
        trades = raw_trade_service.get_trades_by_product(bot.product_id)
        
        if not trades:
            return 0.0
        
        # Calculate net position
        total_bought = sum(float(t.size) for t in trades if t.side == 'BUY')
        total_sold = sum(float(t.size) for t in trades if t.side == 'SELL')
        net_position = total_bought - total_sold
        
        if net_position <= 0:
            return 0.0
        
        # Calculate cost basis
        buy_trades = [t for t in trades if t.side == 'BUY']
        total_cost = sum(float(t.size) * float(t.price) for t in buy_trades)
        avg_buy_price = total_cost / total_bought if total_bought > 0 else 0
        
        # Get current price
        market_service = get_market_data_service()
        current_price = market_service.get_current_price(bot.product_id)
        
        if not current_price or avg_buy_price == 0:
            return 0.0
        
        # Calculate P&L percentage
        pnl_percent = ((current_price - avg_buy_price) / avg_buy_price) * 100
        return pnl_percent
    
    def has_existing_position(self, bot: Bot, db: Session) -> bool:
        """
        Check if bot has existing holdings.
        Migrated from bot_evaluator.py emergency code.
        """
        from backend.app.services.raw_trade_service import RawTradeService
        
        raw_trade_service = RawTradeService(db)
        trades = raw_trade_service.get_trades_by_product(bot.product_id)
        
        if not trades:
            return False
        
        total_bought = sum(float(t.size) for t in trades if t.side == 'BUY')
        total_sold = sum(float(t.size) for t in trades if t.side == 'SELL')
        net_position = total_bought - total_sold
        
        return net_position > 0.0001  # Allow for floating point precision


# Singleton instance
_portfolio_manager_instance = None

def get_portfolio_manager() -> HybridPortfolioDecisionEngine:
    """Get or create singleton portfolio manager instance"""
    global _portfolio_manager_instance
    if _portfolio_manager_instance is None:
        _portfolio_manager_instance = HybridPortfolioDecisionEngine()
    return _portfolio_manager_instance
```

#### 2. `/backend/app/models/portfolio_models.py` (New Database Models)

```python
from sqlalchemy import Column, Integer, String, Float, DateTime, Boolean, ForeignKey, Text
from sqlalchemy.orm import relationship
from datetime import datetime
from backend.app.models.models import Base


class PortfolioAction(Base):
    """Track portfolio management decisions and actions"""
    __tablename__ = "portfolio_actions"
    
    id = Column(Integer, primary_key=True, index=True)
    bot_id = Column(Integer, ForeignKey("bots.id"), nullable=False)
    timestamp = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    # Decision details
    action_type = Column(String(20), nullable=False)  # learn, scale_up, scale_down, liquidate, hold
    rationale = Column(Text, nullable=True)
    
    # Performance data at time of decision
    pnl_usd = Column(Float, nullable=True)
    pnl_percent = Column(Float, nullable=True)
    confidence = Column(Float, nullable=True)
    days_since_profit = Column(Integer, nullable=True)
    
    # Position changes
    old_multiplier = Column(Float, nullable=True)
    new_multiplier = Column(Float, nullable=True)
    
    # Learning changes (JSON serialized)
    learning_changes = Column(Text, nullable=True)
    
    # Execution status
    executed = Column(Boolean, default=False)
    execution_error = Column(Text, nullable=True)
    
    # Relationships
    bot = relationship("Bot", back_populates="portfolio_actions")


class PositionHistory(Base):
    """Track position size changes over time"""
    __tablename__ = "position_history"
    
    id = Column(Integer, primary_key=True, index=True)
    bot_id = Column(Integer, ForeignKey("bots.id"), nullable=False)
    timestamp = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    # Position details
    position_multiplier = Column(Float, nullable=False)
    position_size_usd = Column(Float, nullable=True)
    reason = Column(String(100), nullable=True)
    
    # Performance snapshot
    pnl_usd = Column(Float, nullable=True)
    pnl_percent = Column(Float, nullable=True)
    
    # Relationships
    bot = relationship("Bot", back_populates="position_history")
```

#### 3. `/backend/app/tasks/portfolio_tasks.py` (Celery Tasks)

```python
from celery import shared_task
from backend.app.database import SessionLocal
from backend.app.services.portfolio_manager import get_portfolio_manager
from backend.app.models.models import Bot
from backend.app.models.portfolio_models import PortfolioAction, PositionHistory
from backend.app.services.raw_trade_service import RawTradeService
from backend.app.services.market_data_service import get_market_data_service
import logging
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)


@shared_task(name="tasks.portfolio_evaluation")
def evaluate_portfolio():
    """
    Evaluate entire portfolio and execute portfolio-level decisions.
    Runs every hour (less frequent than bot evaluation).
    """
    db = SessionLocal()
    try:
        logger.info("🎯 Starting portfolio evaluation")
        
        portfolio_manager = get_portfolio_manager()
        bots = db.query(Bot).filter(Bot.is_active == True).all()
        
        actions_taken = []
        
        for bot in bots:
            # Gather performance data
            performance_data = _gather_performance_data(bot, db)
            
            # Get portfolio decision
            decision = portfolio_manager.evaluate_bot_action(bot, performance_data)
            
            # Log decision
            action_record = PortfolioAction(
                bot_id=bot.id,
                action_type=decision['action'],
                rationale=decision['rationale'],
                pnl_usd=performance_data.get('total_pnl_usd'),
                pnl_percent=performance_data.get('pnl_percent'),
                confidence=performance_data.get('confidence'),
                days_since_profit=performance_data.get('days_since_profit')
            )
            
            # Execute action
            if decision['action'] in ['scale_up', 'scale_down', 'liquidate']:
                position_changes = decision.get('position_changes', {})
                action_record.old_multiplier = bot.position_multiplier
                action_record.new_multiplier = position_changes.get('new_multiplier', 1.0)
                
                # Update bot position multiplier
                bot.position_multiplier = position_changes.get('new_multiplier', 1.0)
                
                # Record in history
                position_record = PositionHistory(
                    bot_id=bot.id,
                    position_multiplier=bot.position_multiplier,
                    reason=position_changes.get('reason', decision['action']),
                    pnl_usd=performance_data.get('total_pnl_usd'),
                    pnl_percent=performance_data.get('pnl_percent')
                )
                db.add(position_record)
                
                action_record.executed = True
                actions_taken.append(f"{bot.product_id}: {decision['action']} to {bot.position_multiplier}x")
            
            elif decision['action'] == 'learn':
                # Learning system will handle weight updates
                action_record.executed = True
                actions_taken.append(f"{bot.product_id}: learning activated")
            
            db.add(action_record)
        
        db.commit()
        
        logger.info(f"✅ Portfolio evaluation complete: {len(actions_taken)} actions taken")
        for action in actions_taken:
            logger.info(f"  - {action}")
        
        return {
            'success': True,
            'bots_evaluated': len(bots),
            'actions_taken': len(actions_taken),
            'actions': actions_taken
        }
        
    except Exception as e:
        logger.error(f"❌ Portfolio evaluation failed: {str(e)}")
        db.rollback()
        return {'success': False, 'error': str(e)}
    finally:
        db.close()


def _gather_performance_data(bot: Bot, db) -> dict:
    """Gather all performance metrics for a bot"""
    raw_trade_service = RawTradeService(db)
    market_service = get_market_data_service()
    
    # Get trade history
    trades = raw_trade_service.get_trades_by_product(bot.product_id)
    
    # Calculate P&L
    total_pnl_usd = 0.0
    pnl_percent = 0.0
    
    if trades:
        # Use existing calculation from position service
        position_service = portfolio_manager.position_service
        pnl_percent = position_service.calculate_position_pnl_percent(bot, db)
        
        # Calculate USD P&L
        total_bought = sum(float(t.size) for t in trades if t.side == 'BUY')
        total_sold = sum(float(t.size) for t in trades if t.side == 'SELL')
        net_position = total_bought - total_sold
        
        if net_position > 0:
            buy_trades = [t for t in trades if t.side == 'BUY']
            total_cost = sum(float(t.size) * float(t.price) for t in buy_trades)
            avg_buy_price = total_cost / total_bought if total_bought > 0 else 0
            current_price = market_service.get_current_price(bot.product_id)
            
            if current_price and avg_buy_price:
                total_pnl_usd = (current_price - avg_buy_price) * net_position
    
    # Days since last profit
    profitable_trades = [t for t in trades if t.side == 'SELL']  # Simplification
    days_since_profit = 999
    if profitable_trades:
        last_sell = max(profitable_trades, key=lambda t: t.created_time)
        days_since_profit = (datetime.utcnow() - last_sell.created_time).days
    
    # Confidence from learning system
    confidence = 0.5  # Default, can be enhanced with learning system integration
    
    # Volatility (placeholder - can be enhanced with market data)
    volatility_pct = 100.0
    
    return {
        'total_pnl_usd': total_pnl_usd,
        'pnl_percent': pnl_percent,
        'confidence': confidence,
        'days_since_profit': days_since_profit,
        'volatility_pct': volatility_pct,
        'current_position_size': getattr(bot, 'position_multiplier', 1.0)
    }
```

#### 4. Database Migration Script

**Create**: `/backend/app/alembic/versions/add_portfolio_tables.py`

```python
"""Add portfolio management tables

Revision ID: portfolio_mgmt_001
Revises: previous_revision
Create Date: 2025-10-11

"""
from alembic import op
import sqlalchemy as sa

def upgrade():
    # Add position_multiplier to Bot model
    op.add_column('bots', sa.Column('position_multiplier', sa.Float(), default=1.0))
    
    # Create portfolio_actions table
    op.create_table('portfolio_actions',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('bot_id', sa.Integer(), nullable=False),
        sa.Column('timestamp', sa.DateTime(), nullable=False),
        sa.Column('action_type', sa.String(length=20), nullable=False),
        sa.Column('rationale', sa.Text(), nullable=True),
        sa.Column('pnl_usd', sa.Float(), nullable=True),
        sa.Column('pnl_percent', sa.Float(), nullable=True),
        sa.Column('confidence', sa.Float(), nullable=True),
        sa.Column('days_since_profit', sa.Integer(), nullable=True),
        sa.Column('old_multiplier', sa.Float(), nullable=True),
        sa.Column('new_multiplier', sa.Float(), nullable=True),
        sa.Column('learning_changes', sa.Text(), nullable=True),
        sa.Column('executed', sa.Boolean(), default=False),
        sa.Column('execution_error', sa.Text(), nullable=True),
        sa.ForeignKeyConstraint(['bot_id'], ['bots.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_portfolio_actions_id'), 'portfolio_actions', ['id'], unique=False)
    
    # Create position_history table
    op.create_table('position_history',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('bot_id', sa.Integer(), nullable=False),
        sa.Column('timestamp', sa.DateTime(), nullable=False),
        sa.Column('position_multiplier', sa.Float(), nullable=False),
        sa.Column('position_size_usd', sa.Float(), nullable=True),
        sa.Column('reason', sa.String(length=100), nullable=True),
        sa.Column('pnl_usd', sa.Float(), nullable=True),
        sa.Column('pnl_percent', sa.Float(), nullable=True),
        sa.ForeignKeyConstraint(['bot_id'], ['bots.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_position_history_id'), 'position_history', ['id'], unique=False)

def downgrade():
    op.drop_index(op.f('ix_position_history_id'), table_name='position_history')
    op.drop_table('position_history')
    op.drop_index(op.f('ix_portfolio_actions_id'), table_name='portfolio_actions')
    op.drop_table('portfolio_actions')
    op.drop_column('bots', 'position_multiplier')
```

---

## PART 3: Implementation Timeline

### Week 1: Foundation (Days 1-3)

**Day 1: Code Cleanup + Setup (4 hours)**
- [ ] Remove Phase 9A emergency code from bot_evaluator.py
- [ ] Create portfolio_manager.py skeleton
- [ ] Create portfolio_models.py
- [ ] Update Bot model relationships

**Day 2: Core Logic (6 hours)**
- [ ] Implement HybridPortfolioSettings
- [ ] Implement PositionScalingService
- [ ] Migrate P&L calculation utilities
- [ ] Unit tests for scaling calculations

**Day 3: Decision Engine (6 hours)**
- [ ] Implement HybridPortfolioDecisionEngine
- [ ] Integration with learning system
- [ ] Unit tests for decision logic
- [ ] Test with current 27 positions

### Week 2: Integration (Days 4-7)

**Day 4: Database Migration (3 hours)**
- [ ] Create migration script
- [ ] Run migration on dev database
- [ ] Verify schema changes
- [ ] Backup production database

**Day 5: Celery Tasks (4 hours)**
- [ ] Implement portfolio_evaluation_task
- [ ] Add to Celery beat schedule (every hour)
- [ ] Test task execution
- [ ] Monitor first run

**Day 6: Testing & Validation (6 hours)**
- [ ] End-to-end testing with live data
- [ ] Validate scaling calculations
- [ ] Test emergency liquidation logic
- [ ] Performance monitoring

**Day 7: Documentation & Deployment (4 hours)**
- [ ] Update documentation
- [ ] Create operator guide
- [ ] Deploy to production
- [ ] Monitor first 24 hours

---

## PART 4: Success Metrics

### Immediate (Week 1)
- ✅ Code cleanup complete (0 Phase 9A references)
- ✅ Portfolio manager service created
- ✅ Unit tests passing (95%+ coverage)

### Short-term (Week 2)
- ✅ Database migration successful
- ✅ Celery task running every hour
- ✅ First portfolio actions recorded
- ✅ 0 system errors during deployment

### Medium-term (Weeks 3-4)
- 🎯 Reduce losing positions from 27 to <15
- 🎯 Scale up 3+ winning positions (momentum detected)
- 🎯 Emergency liquidation prevents losses >$40
- 🎯 Portfolio P&L improving week-over-week

### Long-term (Month 2+)
- 🎯 Portfolio P&L positive (+$100+ target)
- 🎯 60%+ bots profitable (from current 33%)
- 🎯 Dynamic scaling active on 10+ positions
- 🎯 Learning system + scaling hybrid proven effective

---

## PART 5: Next Steps

**Immediate Decision Required:**
1. Approve cleanup plan (remove Phase 9A code)
2. Approve architecture (portfolio_manager.py structure)
3. Set timeline (1 week vs 2 weeks)

**Then Execute:**
1. Day 1 cleanup (30 min - 1 hour)
2. Day 2-3 core implementation (12 hours)
3. Week 2 integration (17 hours)

**Total Estimated Effort**: 30-35 hours across 7 days

---

## Questions for User

1. **Timeline**: Prefer 1-week intensive or 2-week gradual?
2. **Risk Tolerance**: Start with conservative settings (max 1.5x scaling) or aggressive (3x scaling)?
3. **Emergency Actions**: Auto-liquidate at -$40 loss or require manual approval?
4. **Testing**: Test on subset of bots first or deploy to all 27?

