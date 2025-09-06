# Bot-Centric Coinbase Trading System - AI Agent Guide

## 🚀 **IMMEDIATE PRODUCTIVITY ESSENTIALS**

### **Critical First Commands**
```bash
./scripts/status.sh   # Check if system is running (all should be ✅)
./scripts/start.sh    # Start all services if needed
curl -s http://localhost:8000/api/v1/bots/status/summary | python3 -m json.tool  # View live bot status
```

### **Current System Status (September 5, 2025)**
- ✅ **Trading System Operational**: 2,870 trades executed (92.7% success rate)
- ✅ **Two Production Bots**: BTC Continuous Trader (HOT 🔥), ETH Continuous Trader (HOT 🔥) - Strong signals but blocked
- ✅ **Test Suite**: 82 total tests (80 passing, 2 failing - documented issues)
- ✅ **Service Health**: All services operational (Redis, Backend, Frontend, Celery)
- ✅ **Performance**: Sub-100ms API response times, 0.4% memory usage
- ✅ **Enhanced Status API**: `/api/v1/bots/status/enhanced` with trading_intent, confirmation, trade_readiness
- ⚠️ **CRITICAL ISSUE**: Both bots blocked by insufficient funds ($2.25 available, $10 required)
- ⚠️ **INFORMATION FEEDBACK**: Trade data pipeline broken - missing action fields, $0.00 amounts
- 🎯 **CURRENT FOCUS**: Information feedback pipeline fix → Dashboard UX enhancement → Balance management

## 🎯 **ARCHITECTURE ESSENTIALS**

### **Bot-Centric Design**
- **One bot per trading pair** with weighted signal aggregation
- **Signal scoring**: -1 (strong sell) to +1 (strong buy)
- **Temperature indicators**: HOT 🔥/WARM 🌡️/COOL ❄️/FROZEN 🧊
- **Weight validation**: Signal weights must be ≤ 1.0 (API enforced)
- **Signal confirmation**: Time-based validation prevents false signals
- **JSON signal config**: Stored as TEXT in database, parsed for evaluation

### **Data Flow Architecture**
```
Market Data → Signal Evaluation → Temperature Calculation → UI Display
     ↓              ↓                      ↓                 ↓
Coinbase API → BotSignalEvaluator → calculate_bot_temperature → TanStack Query
```

### **Real-Time Data Flow**
- **Frontend**: TanStack Query polling every 5 seconds
- **Backend**: Fresh market evaluation on each API request  
- **Temperature calculation**: Unified source in `app/utils/temperature.py`
- **UI updates**: Automatic without manual refresh
- **Enhanced Status Pipeline**: trading_intent → confirmation → trade_readiness → execution
- **Position Management**: Tranche tracking with real-time P&L calculation

### **Service Architecture**
```
Backend: FastAPI + SQLAlchemy + Celery + Redis
Database: SQLite with Bot/BotSignalHistory/Trade models  
Frontend: React 18 + TypeScript + TailwindCSS + TanStack Query
Trading: Coinbase Advanced Trade API (JWT auth) - LIVE TRADING ACTIVE
Real Orders: Actual buy/sell orders placed on Coinbase Pro
```

## 🔧 **CRITICAL COMMANDS & VERIFICATION**

### **Service Management**
```bash
./scripts/start.sh     # Start all services with health checks
./scripts/status.sh    # Check service health and resource usage
./scripts/test.sh      # Run 104-test comprehensive suite
./scripts/logs.sh      # View application logs with filtering
```

### **Live System Verification**
```bash
# Check bot temperatures and enhanced status
curl -s "http://localhost:8000/api/v1/bots/status/enhanced" | python3 -m json.tool

# Expected: Enhanced data with trading_intent, confirmation, trade_readiness fields
# Current status: Both bots HOT 🔥 but blocked by insufficient balance

# Verify trade statistics and system performance
curl -s "http://localhost:8000/api/v1/trades/stats" | python3 -m json.tool

# Expected: 2,870 total trades with 92.7% success rate

# Check balance status blocking trades
curl -s "http://localhost:8000/api/v1/bots/status/enhanced" | python3 -c "
import sys, json
data = json.load(sys.stdin)
for bot in data:
    readiness = bot.get('trade_readiness', {})
    print(f'Bot {bot[\"id\"]}: {bot[\"temperature\"]} - Can Trade: {readiness.get(\"can_trade\", False)}')
    if readiness.get('blocking_reason'):
        print(f'  Blocked: {readiness[\"blocking_reason\"]}')
"

# Verify UI auto-updates
open http://localhost:3000  # Values should change every 5 seconds
```

## 📊 **KEY API ENDPOINTS**

### **Primary Bot API** (Main Interface)
- `GET /api/v1/bots/` - List all bots
- `POST /api/v1/bots/` - Create bot with signal configuration
- `GET /api/v1/bots/status/summary` - Live bot status (fresh evaluations)
- `GET /api/v1/bots/status/enhanced` - Enhanced status with trading_intent, confirmation, trade_readiness
- `PUT /api/v1/bots/{id}` - Update bot configuration
- `POST /api/v1/bots/{id}/start` - Start bot
- `POST /api/v1/bots/{id}/stop` - Stop bot

### **Signal & Temperature APIs**
- `POST /api/v1/bot-evaluation/{id}/evaluate` - Evaluate bot signals with automatic trading
- `GET /api/v1/bots/{id}/confirmation-status` - Signal confirmation status
- `GET /api/v1/bot-temperatures/dashboard` - Temperature summary

### **Market Data APIs**
- `GET /api/v1/market/ticker/{product_id}` - Live ticker data
- `GET /api/v1/market/accounts` - Account balances (uses portfolio breakdown)

### **Trading Safety & Execution APIs (Phase 4.2.1)**
- `POST /api/v1/trades/validate-trade` - Validate trade against safety limits
- `GET /api/v1/trades/safety-status` - Current safety status and limits
- `POST /api/v1/trades/emergency-stop` - Emergency halt all trading
- `GET /api/v1/trades/` - List all trades with actual Coinbase order IDs
- `GET /api/v1/trades/recent/{bot_id}` - Recent trades for specific bot

### **Continuous Trading APIs (Active)**
- `POST /api/v1/bot-evaluation/{id}/evaluate` - Now includes automatic trade execution
- `POST /api/v1/bot-evaluation/{id}/simulate-automatic-trade` - Test trading pipeline

## ⚠️ **CRITICAL LESSONS LEARNED**

### **Development Environment**
- **Backend**: Python 3.10.12 in `backend/venv/` virtual environment
- **Frontend**: Node.js v20.18.0 with Vite + React 18
- **Database**: SQLite (`backend/trader.db`) - single file, no setup needed
- **Redis**: Docker container managed by `docker-compose.yml`
- **Process Management**: All services run as background processes with PID tracking
- **Test Suite**: 82 tests with ~14 second execution time (includes Phase 4 trading tests)

### **Real-Time Architecture Patterns**
- **Polling > WebSocket**: Simple 5-second polling more reliable than complex WebSocket
- **Fresh Evaluations**: Backend must calculate live, not use cached `bot.current_combined_score`
- **Temperature Enums**: Frontend must match backend exactly ('COOL' not 'COLD')
- **Reactive Keys**: Use changing data in React keys to force re-renders

### **Common Pitfalls to Avoid**
1. **Using stale cached data**: Always perform fresh market evaluations
2. **Temperature enum mismatch**: Backend returns 'COOL', not 'COLD'
3. **Signal weight errors**: Total enabled weights must be ≤ 1.0
4. **USD account access**: Use portfolio breakdown, NOT `get_accounts()`
5. **Test bot pollution**: Always clean up test bots after test runs

### **Critical Development Patterns**
- **Enhanced Status First**: Always use `/api/v1/bots/status/enhanced` for comprehensive bot data
- **Position-Aware Trading**: Consider existing tranches before new trade decisions
- **Safety Integration**: All trading actions must go through TradingSafetyService validation
- **Mock Mode Development**: Use TRADING_MODE=mock for safe development, production for live trading
- **Fresh Data Architecture**: Backend evaluations must use live market data, never cached bot scores
- **Tranche Strategy Selection**: Choose appropriate position sizing strategy based on bot configuration

### **Essential Code Patterns**
```python
# ✅ CORRECT: Fresh evaluation pattern
temp_data = evaluator.calculate_bot_temperature(bot, fresh_market_data)
temperature = temp_data.get('temperature', 'FROZEN')

# ✅ CORRECT: Enhanced status access with all fields
curl -s "http://localhost:8000/api/v1/bots/status/enhanced"
# Returns: trading_intent, confirmation, trade_readiness, last_trade

# ✅ CORRECT: USD account access
portfolios = client.get_portfolios()
breakdown = client.get_portfolio_breakdown(portfolio_uuid=portfolios[0]['uuid'])

# ✅ CORRECT: Position service integration
position_service = PositionService(db)
position_summary = position_service.get_position_summary(bot_id)

# ✅ CORRECT: Signal config parsing (from JSON TEXT in database)
signal_config = json.loads(bot.signal_config)
rsi_config = signal_config.get('RSI', {})
if rsi_config.get('enabled', False):
    weight = rsi_config.get('weight', 0.0)

# ✅ CORRECT: Virtual environment usage
# Always use project scripts instead of direct python commands:
./scripts/test.sh          # Not: python -m pytest
./scripts/start.sh         # Not: python app/main.py
source backend/venv/bin/activate  # For manual venv activation

# ✅ CORRECT: Signal config parsing (from JSON TEXT in database)
signal_config = json.loads(bot.signal_config)
rsi_config = signal_config.get('RSI', {})
if rsi_config.get('enabled', False):
    weight = rsi_config.get('weight', 0.0)

# ✅ CORRECT: Virtual environment usage
# Always use project scripts instead of direct python commands:
./scripts/test.sh          # Not: python -m pytest
./scripts/start.sh         # Not: python app/main.py
source backend/venv/bin/activate  # For manual venv activation
```

```typescript
// ✅ CORRECT: Enhanced status polling configuration
export const useBotsStatusEnhanced = () => {
  return useQuery({
    queryKey: ['bots', 'status', 'enhanced'],
    queryFn: () => fetch('/api/v1/bots/status/enhanced').then(r => r.json()),
    refetchInterval: 5000,
    refetchIntervalInBackground: true,
    staleTime: 0,
  });
};

// ✅ CORRECT: Enhanced status data structure access
{bots.map(bot => (
  <div key={`${bot.id}-${bot.current_combined_score}`}>
    <span>{bot.temperature === 'HOT' ? '🔥' : bot.temperature === 'FROZEN' ? '🧊' : '❄️'}</span>
    <span>Action: {bot.trading_intent?.next_action || 'hold'}</span>
    <span>Ready: {bot.trade_readiness?.can_trade ? '✅' : '⛔'}</span>
    {bot.trade_readiness?.blocking_reason && 
      <span>Blocked: {bot.trade_readiness.blocking_reason}</span>
    }
  </div>
))}
```

## 🗂️ **ESSENTIAL FILE LOCATIONS**

### **Key Backend Files**
- `app/utils/temperature.py` - **Unified temperature calculation**
- `app/services/bot_evaluator.py` - Signal aggregation engine with automated trading
- `app/api/bots.py` - Primary bot management API with enhanced status endpoint
- `app/models/models.py` - Database schema (Bot, BotSignalHistory, Trade with enhanced fields)
- `app/services/coinbase_service.py` - External API integration
- `app/services/trading_service.py` - Trade execution service with safety integration
- `app/services/trading_safety.py` - Trading safety validation service
- `app/services/position_service.py` - Enhanced position management with tranche tracking
- `app/services/signals/` - Individual signal implementations (RSI, MA, MACD)
- `backend/venv/` - **Virtual environment** (use project scripts, not direct python)

### **Signal Configuration Pattern**
```python
# Bot signal_config stored as JSON TEXT in database:
{
  "RSI": {"weight": 0.4, "period": 14, "oversold": 30, "overbought": 70, "enabled": true},
  "MA": {"weight": 0.3, "short_period": 10, "long_period": 20, "enabled": true},
  "MACD": {"weight": 0.3, "fast": 12, "slow": 26, "signal": 9, "enabled": true}
}
# Total enabled weights must be ≤ 1.0 (enforced by API validation)
```

### **Enhanced Trade Model (Phase 4.1.3)**
```python
# Trade table includes advanced position management:
class Trade(Base):
    # Basic fields: id, bot_id, product_id, side, size, price, fee, order_id, status
    # Signal tracking: combined_signal_score, signal_scores (JSON)
    # Enhanced position management:
    position_tranches = Column(Text)  # JSON array of position tranches
    average_entry_price = Column(Numeric(precision=20, scale=8))
    tranche_number = Column(Integer, default=1)
    position_status = Column(String(20), default="CLOSED")  # CLOSED, BUILDING, OPEN, REDUCING
    size_usd = Column(Float)  # Trade size in USD
```

### **Tranche-Based Position Management System**

#### **Position Tranche Structure**
```python
# position_tranches JSON structure in Trade model:
{
  "tranches": [
    {
      "tranche_id": 1,
      "entry_price": 43250.0,
      "size_crypto": 0.0023,
      "size_usd": 100.0,
      "timestamp": "2025-09-05T12:00:00Z",
      "status": "filled",
      "exit_price": null,          # Null until position closed
      "pnl": 0.0                   # Unrealized P&L
    }
  ],
  "strategy": "equal_size",        # equal_size, pyramid_up, pyramid_down, adaptive
  "total_invested": 100.0,
  "average_entry": 43250.0,
  "current_pnl": 0.0
}
```

#### **Position Management Strategies**
```python
# Available in PositionService.calculate_next_tranche_size()
TRANCHE_STRATEGIES = {
    "equal_size": "Same USD amount for each tranche",
    "pyramid_up": "Increase size as price moves against position", 
    "pyramid_down": "Decrease size as price moves against position",
    "adaptive": "AI-driven size based on signal strength and market conditions"
}

# Strategy Implementation Example:
def calculate_tranche_size(self, bot_id: int, strategy: str, signal_strength: float):
    if strategy == "equal_size":
        return self.base_position_size
    elif strategy == "pyramid_up":
        return self.base_position_size * (1 + 0.2 * tranche_number)
    elif strategy == "adaptive":
        return self.base_position_size * (0.5 + signal_strength)
```

#### **Position Service Integration Patterns**
```python
# ✅ CORRECT: Position management workflow
position_service = PositionService(db)

# Get current position summary
position_summary = position_service.get_position_summary(bot_id)
# Returns: total_invested, current_value, unrealized_pnl, tranche_count

# Calculate optimal next tranche
next_tranche = position_service.calculate_next_tranche_size(
    bot_id=3,
    current_price=43000.0,
    signal_strength=0.8,
    strategy="adaptive"
)

# Analyze position performance
performance = position_service.analyze_position_performance(bot_id, current_price)
# Returns: roi_percentage, best_entry, worst_entry, efficiency_score

# DCA (Dollar Cost Average) metrics
dca_metrics = position_service.calculate_dollar_cost_average_metrics(
    bot_id, current_price, proposed_investment
)
# Returns: new_average_price, impact_on_breakeven, recommended_action
```

#### **Advanced Position Analytics**
```python
# Position efficiency scoring (0-100)
def calculate_position_efficiency(self, bot_id: int) -> Dict:
    return {
        "efficiency_score": 85,        # How well-timed were entries
        "dca_effectiveness": 92,       # DCA strategy performance
        "risk_adjusted_return": 78,    # Return vs volatility
        "timing_score": 88,            # Entry timing quality
        "size_optimization": 81        # Position sizing effectiveness
    }

# Smart exit recommendations
def recommend_exit_strategy(self, bot_id: int, current_price: float) -> Dict:
    return {
        "action": "partial_exit",               # hold, partial_exit, full_exit
        "recommended_size": 0.3,                # Fraction to exit (0.0-1.0)
        "target_price": 45000.0,                # Optimal exit price
        "confidence": 0.82,                     # Algorithm confidence
        "reasoning": "Take profits at resistance level"
    }
```

### **Key Frontend Files**
- `src/hooks/useBots.ts` - Bot management with TanStack Query
- `src/pages/Dashboard.tsx` - Main dashboard with real-time updates
- `src/components/BotForm.tsx` - Bot creation/editing forms

### **Documentation**
- `PROJECT_STATUS.md` - Current status and next phase readiness
- `docs/IMPLEMENTATION_GUIDE.md` - Detailed technical patterns
- `docs/TROUBLESHOOTING_PLAYBOOK.md` - Debug solutions
- `docs/PHASE_HISTORY.md` - Complete development history

## 🧪 **TESTING & VALIDATION**

### **Test Execution**
```bash
./scripts/test.sh              # Run all 82 tests (80 passing, 2 failing - documented)
./scripts/test.sh --unit       # Signal processing only  
./scripts/test.sh --integration # API and database tests
```

### **Test Coverage Areas**
- **Bot CRUD Operations**: 21 tests (creation, validation, parameters)
- **Signal Processing**: 15 tests (RSI, MA, MACD calculations)
- **Confirmation System**: 16 tests (time-based signal validation)
- **Temperature System**: 15 tests (unified calculation, thresholds)
- **Live API Integration**: 7 tests (real Coinbase endpoints)
- **Phase 4 Trading Integration**: 8 tests (automated trading, position management)

### **Test Quality Principles**
- **Live API Testing**: Uses real Coinbase API endpoints
- **Automatic Cleanup**: Test bots removed after each run
- **Performance**: ~14 seconds for full 82-test suite
- **Real Data**: Tests use actual market conditions
- **Comprehensive Coverage**: All Phase 4 features tested
- **Integration Focus**: Real-world usage patterns validated

### **Critical Testing Patterns**
```python
# ✅ CORRECT: Test cleanup pattern
def test_parameter_ranges(self, client):
    created_bot_ids = []
    try:
        # Test logic
        if response.status_code == 201:
            created_bot_ids.append(response.json()["id"])
    finally:
        # Always clean up
        for bot_id in created_bot_ids:
            client.delete(f"/api/v1/bots/{bot_id}")
```

## � **CURRENT IMPLEMENTATION FOCUS**

### **Enhanced Status API Implemented (September 5, 2025)**
- ✅ **Enhanced Bot Status**: `/api/v1/bots/status/enhanced` provides trading_intent, confirmation, trade_readiness
- ✅ **Trading Intent Display**: next_action, signal_strength, confidence metrics
- ✅ **Confirmation Tracking**: Real-time confirmation progress and timing
- ✅ **Trade Readiness**: Clear status with blocking reasons (balance, cooldown, etc.)

### **CURRENT PRIORITY ROADMAP**

#### **Phase 1: Dashboard UX Enhancement (1-2 days) - HIGH PRIORITY**
- **Balance Management UI**: Clear indication when trades blocked by insufficient funds
- **Trading Intent Display**: Visual indicators for BUY/SELL/HOLD readiness with signal strength meters
- **Activity Timeline**: Meaningful recent activity feed with actual trade outcomes and P&L
- **Confirmation Timers**: Live countdown when signals are confirming (circular progress indicators)
- **Professional Trading Interface**: TradingView-style price action display with bot overlay
- **Risk Visualization**: Position size vs account balance with safety limit indicators
- **Expected Outcome**: User confidence through clear system state visibility

#### **Phase 2: Information Feedback Pipeline (2-3 days) - MEDIUM PRIORITY**
- **Trade Data Enhancement**: Ensure complete trade records with action, amount fields
- **Real-time Trade Status**: Live updates during trade execution
- **Status Synchronization**: Connect enhanced status with trade outcomes
- **Expected Outcome**: Complete visibility into trading activity

#### **Phase 3: Advanced Strategy Framework (1 week) - FUTURE**
- **Enhanced Testing Infrastructure**: Market data generation for strategy validation
- **Multi-timeframe Analysis**: Cross-timeframe signal confirmation
- **Strategy Backtesting**: Historical performance validation

## 🎨 **DASHBOARD UX DESIGN PATTERNS**

### **Professional Trading Interface Recommendations**

#### **Information Hierarchy for Trading Decisions**
```typescript
// Primary Information (Always Visible)
interface BotStatusPrimary {
  actionIntent: "BUY" | "SELL" | "HOLD";           // Large, color-coded
  signalStrength: number;                          // 0-1 visual meter
  tradeReadiness: "ready" | "confirming" | "blocked" | "cooldown";
  balanceStatus: "sufficient" | "low" | "insufficient";
}

// Secondary Information (Contextual)
interface BotStatusSecondary {
  confirmationProgress: number;                     // Circular progress 0-100%
  lastTradeOutcome: "profit" | "loss" | "pending"; // Green/Red/Yellow indicator
  positionSize: number;                            // Current USD position
  recentPerformance: number;                       // 24h P&L percentage
}
```

#### **Visual Design Patterns**
- **Signal Strength Meters**: Horizontal bars with threshold lines (like TradingView RSI)
- **Confirmation Timers**: Circular progress indicators with remaining time
- **Balance Warnings**: Yellow/Red alert badges when insufficient funds
- **Position Visualization**: Progress bars showing current position vs max position
- **Temperature Icons**: 🔥🌡️❄️🧊 with signal strength gradient backgrounds
- **Action Buttons**: Large, prominent BUY/SELL buttons when ready (disabled when blocked)

#### **Activity Feed Design**
```typescript
interface TradingActivity {
  type: "trade_executed" | "signal_confirmed" | "balance_warning" | "position_closed";
  timestamp: Date;
  outcome: "success" | "failure" | "warning" | "info";
  message: string;                                 // Human-readable summary
  details: {
    amount?: number;                               // Trade amount in USD
    price?: number;                                // Execution price
    pnl?: number;                                  // Profit/loss for closed positions
    signalScore?: number;                          // Signal strength at time
  };
}
```

#### **Risk Management Visual Indicators**
- **Account Balance Gauge**: Circular gauge showing available vs required funds
- **Daily Loss Limit**: Progress bar approaching safety limits
- **Position Heat Map**: Color-coded position sizes across all bots
- **Safety Circuit Status**: Green/Yellow/Red status indicators for emergency stops

#### **Real-time Data Display Patterns**
- **Live Price Tickers**: Streaming price updates with change indicators
- **Signal Score Graphs**: Mini-charts showing signal evolution over time
- **Confirmation Countdowns**: Live timers with millisecond precision
- **WebSocket Connection Status**: Connection health indicators

## 🔍 **TROUBLESHOOTING QUICK REFERENCE**

### **UI Not Updating**
1. Check browser Network tab for 5-second `/bots/status/summary` requests
2. Verify backend returns different scores between calls
3. Ensure React components use reactive keys with changing data
4. Check temperature enum consistency ('COOL' not 'COLD')

### **Service Issues**
1. Check port conflicts: `lsof -i :8000`, `lsof -i :3000`
2. Verify virtual environment: `which python` (should show venv path)
3. Test connectivity: `curl http://localhost:8000/health`
4. Use management scripts: `./scripts/restart.sh`

### **Test Failures**
1. Clean up test bots: Look for test bot names in database
2. Check Coinbase API: Avoid slow SDK introspection patterns
3. Verify fresh data: Ensure tests use live market data, not cached

---

## 📚 **COMPREHENSIVE DOCUMENTATION LINKS**

For detailed information beyond this essential guide:

- **[MASTER ROADMAP](../docs/IMPLEMENTATION_ROADMAP_SEPTEMBER_2025.md)** - **COMPREHENSIVE STRATEGIC PLAN** - Your complete implementation roadmap
- **[Codebase Analysis](../docs/CODEBASE_ANALYSIS_SEPTEMBER_2025.md)** - Complete system assessment with critical issues identified
- **[Information Feedback Issues](../docs/INFORMATION_FEEDBACK_ISSUES.md)** - Critical pipeline problems requiring immediate fix
- **[Dashboard UX Redesign](../docs/DASHBOARD_UX_REDESIGN.md)** - UX improvements for better control and visibility
- **[Implementation Guide](../docs/IMPLEMENTATION_GUIDE.md)** - Technical patterns, code specifics
- **[Troubleshooting Playbook](../docs/TROUBLESHOOTING_PLAYBOOK.md)** - Debug solutions  
- **[Phase History](../docs/PHASE_HISTORY.md)** - Complete development timeline
- **[Project Status](../PROJECT_STATUS.md)** - Current state and next phase readiness

---
*AI Agent Instructions - Essential Guide*  
*Last Updated: September 5, 2025*  
*CURRENT FOCUS: Dashboard UX Enhancement → Information Feedback Pipeline → Advanced Strategy Framework*
