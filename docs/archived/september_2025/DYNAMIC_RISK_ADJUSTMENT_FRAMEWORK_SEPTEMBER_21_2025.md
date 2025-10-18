# Dynamic Risk Adjustment Framework
## Implementation Specification - September 21, 2025

### 🎯 **Overview**

Based on 24-hour production test analysis showing **+$381.67 total profit** with significant performance variance across trading pairs, we are implementing a **Dynamic Risk Adjustment Framework** that automatically scales position sizes based on real-time performance signals rather than manual intervention.

### 📊 **Problem Statement**

**Current Performance Analysis (24hr test):**
- **AVNT-USD**: +$404.68 (315 trades) = $1.285/trade
- **ETH-USD**: -$10.88 (227 trades) = -$0.048/trade  
- **BTC-USD**: -$4.37 (148 trades) = -$0.030/trade
- **XRP-USD**: +$0.75 (44 trades) = +$0.017/trade

**Key Insights:**
- AVNT carried the portfolio (+$404.68 vs -$23.01 for everything else)
- High signal strength (0.92) correlated with high profitability
- Low confidence pairs (ETH: 0.21) showed consistent losses
- Manual bot adjustment is not scalable

### 🧠 **Framework Design**

#### **Core Philosophy**
Instead of manually pausing/scaling bots, implement an **adaptive risk multiplier** that automatically adjusts based on:
1. **Signal Strength** (existing system data)
2. **Confidence Level** (existing system data)  
3. **Recent Performance** (last 50 trades P&L)

#### **Risk Calculation Formula**
```python
def calculate_risk_multiplier(bot):
    # Signal component (weighted heavily - 2x)
    signal_component = min(bot.signal_strength * 2.0, 2.0)
    
    # Confidence component (weighted lightly - 0.5x)
    confidence_component = bot.confidence * 0.5
    
    # Performance component (last 50 trades)
    recent_performance = bot.last_50_trades_avg_pnl
    performance_multiplier = 1.0 + (recent_performance * 10)  # $0.10 profit = 2x
    
    # Final calculation with bounds
    risk_multiplier = (signal_component + confidence_component) * performance_multiplier
    return max(0.2, min(3.0, risk_multiplier))  # Cap between 0.2x and 3.0x
```

#### **Risk Categories & Multipliers**

| Signal Strength | Confidence | Performance (50-trade avg) | Risk Multiplier | Example |
|----------------|------------|---------------------------|-----------------|---------|
| >0.8 | Any | >$0.50/trade | 3.0x (max) | AVNT current state |
| >0.8 | Any | $0.10-$0.50/trade | 2.0-2.8x | Strong momentum |
| 0.5-0.8 | >0.5 | >$0.05/trade | 1.0-1.5x | Normal operation |
| 0.5-0.8 | <0.5 | <$0.05/trade | 0.3-0.7x | ETH current state |
| <0.5 | Any | Any | 0.2x (min) | Defensive mode |

### 📋 **Implementation Plan**

#### **Phase 1: Data Collection Enhancement**
1. **Add performance tracking** for last 50 trades per bot
2. **Implement P&L rolling average** calculation
3. **Create risk multiplier calculation service**

#### **Phase 2: Position Sizing Integration**
1. **Modify position sizing logic** to use risk multiplier
2. **Apply multiplier to base position sizes**
3. **Add safety bounds** (0.2x to 3.0x range)

#### **Phase 3: Real-time Adjustment**
1. **Recalculate risk multiplier** every 10 trades or 1 hour
2. **Apply adjustments** to subsequent trade sizing
3. **Log all risk adjustments** for analysis

#### **Phase 4: Monitoring & Validation**
1. **Track performance impact** of dynamic sizing
2. **Compare results** vs static sizing
3. **Refine multiplier formula** based on results

### 🔧 **Technical Implementation**

#### **New Database Fields**
```sql
-- Add to bots table
ALTER TABLE bots ADD COLUMN current_risk_multiplier DECIMAL(3,2) DEFAULT 1.0;
ALTER TABLE bots ADD COLUMN last_risk_calculation TIMESTAMP;
ALTER TABLE bots ADD COLUMN last_50_trades_pnl DECIMAL(10,2) DEFAULT 0.0;
```

#### **New Service: RiskAdjustmentService**
```python
class RiskAdjustmentService:
    def __init__(self, db_session):
        self.db = db_session
    
    def calculate_risk_multiplier(self, bot_id: int) -> float:
        # Implementation per formula above
        
    def update_bot_risk_multiplier(self, bot_id: int):
        # Update bot's risk multiplier in database
        
    def get_adjusted_position_size(self, bot_id: int, base_size: float) -> float:
        # Apply risk multiplier to base position size
```

#### **Integration Points**
1. **Position sizing calculations** in trading execution
2. **Bot status API** to show current risk multipliers
3. **Risk adjustment logging** for performance analysis

### 📈 **Expected Outcomes**

#### **Immediate Benefits**
- **AVNT-style winners** get 2-3x position sizes automatically
- **ETH-style losers** get reduced to 0.3x sizes automatically
- **No manual intervention** required

#### **Performance Projections**
Based on current data:
- **AVNT at 3x sizing**: $1.285 → $3.855 per trade potential
- **ETH at 0.3x sizing**: -$0.048 → -$0.014 per trade (reduced losses)
- **Net effect**: Amplify winners, minimize losers

#### **Risk Management**
- **Maximum exposure cap**: 3x prevents over-leveraging
- **Minimum exposure floor**: 0.2x prevents complete shutdown
- **Rolling assessment**: 50-trade window prevents overreaction

### 🎯 **Success Metrics**

1. **Overall P&L improvement** vs baseline
2. **Risk-adjusted returns** (Sharpe ratio improvement)
3. **Reduced manual intervention** requirements
4. **Faster adaptation** to market conditions

### 📋 **Next Steps**

1. **Review and approve** this framework specification
2. **Implement Phase 1** (data collection enhancement)
3. **Test in sandbox** environment with paper trading
4. **Deploy to production** with monitoring
5. **Iterate and optimize** based on results

---

**Document Status**: Draft for Review  
**Author**: System Analysis Team  
**Date**: September 21, 2025  
**Related**: 24-Hour Production Test Analysis (+$381.67 profit)