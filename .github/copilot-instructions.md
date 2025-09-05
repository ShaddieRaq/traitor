# Bot-Centric Coinbase Trading System - AI Agent Guide

## 🚀 **IMMEDIATE PRODUCTIVITY ESSENTIALS**

### **Critical First Commands**
```bash
./scripts/status.sh   # Check if system is running (all should be ✅)
./scripts/start.sh    # Start all services if needed
curl -s http://localhost:8000/api/v1/bots/status/summary | python3 -m json.tool  # View live bot status
```

### **Current System Status (September 4, 2025)**
- ✅ **Phase 4.2.1 Complete**: Automated Trading Integration - Continuous Trading Operational
- ✅ **Real Trading Execution**: Two production bots executing live Coinbase trades
- ✅ **Continuous Trading Verified**: BTC Continuous Trader (COOL ❄️), ETH Continuous Trader (HOT 🔥) 
- ✅ **Automatic Trade Execution**: Signal evaluation → confirmation → live trade placement
- ✅ **Production Database**: 2,530 trades recorded with actual Coinbase order IDs (99.6% success rate)
- ✅ **Live Position Management**: Current positions tracked (BTC: $38.10, ETH: $74.98)
- ✅ **82/82 tests passing** (100% success rate, <8 seconds execution)
- ✅ **Live UI Updates**: Bot temperatures and scores update every 5 seconds
- ✅ **Real-time Trading Pipeline**: Fully automated signal-to-trade execution
- ✅ **Production-Ready System**: Clean codebase with active trading operations

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
# Check bot temperatures (should show live values)
curl -s "http://localhost:8000/api/v1/bots/status/summary" | python3 -m json.tool

# Expected results (Sept 4, 2025):
# BTC Continuous Trader: COOL ❄️ (score: ~0.012, continuous trading)
# ETH Continuous Trader: HOT 🔥 (score: ~-0.358, continuous trading)

# Verify trade statistics and system performance
curl -s "http://localhost:8000/api/v1/trades/stats" | python3 -m json.tool

# Expected: 2,530+ total trades with 99.6% success rate

# Verify UI auto-updates
open http://localhost:3000  # Values should change every 5 seconds

# Check recent live trades (limited to 100 by default)
curl -s "http://localhost:8000/api/v1/trades/" | python3 -c "import sys, json; data = json.load(sys.stdin); print(f'Recent {len(data)} trades loaded')"
```

## 📊 **KEY API ENDPOINTS**

### **Primary Bot API** (Main Interface)
- `GET /api/v1/bots/` - List all bots
- `POST /api/v1/bots/` - Create bot with signal configuration
- `GET /api/v1/bots/status/summary` - Live bot status (fresh evaluations)
- `PUT /api/v1/bots/{id}` - Update bot configuration
- `POST /api/v1/bots/{id}/start` - Start bot
- `POST /api/v1/bots/{id}/stop` - Stop bot

### **Signal & Temperature APIs**
- `POST /api/v1/bot-evaluation/{id}/evaluate` - Evaluate bot signals  
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
- **Test Suite**: 82 tests with <8 second execution time (includes Phase 4 trading tests)

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

### **Essential Code Patterns**
```python
# ✅ CORRECT: Fresh evaluation pattern
temp_data = evaluator.calculate_bot_temperature(bot, fresh_market_data)
temperature = temp_data.get('temperature', 'FROZEN')

# ✅ CORRECT: Temperature calculation
from app.utils.temperature import calculate_bot_temperature

# ✅ CORRECT: USD account access
portfolios = client.get_portfolios()
breakdown = client.get_portfolio_breakdown(portfolio_uuid=portfolios[0]['uuid'])

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
// ✅ CORRECT: Aggressive polling configuration
export const useBotsStatus = () => {
  return useQuery({
    queryKey: ['bots', 'status'],
    queryFn: fetchBotsStatus,
    refetchInterval: 5000,
    refetchIntervalInBackground: true,
    staleTime: 0,
  });
};

// ✅ CORRECT: Reactive component keys
{bots.map(bot => (
  <div key={`${bot.id}-${bot.current_combined_score}`}>
    {bot.temperature === 'HOT' ? '🔥' : bot.temperature === 'COOL' ? '❄️' : '🧊'}
  </div>
))}
```

## 🗂️ **ESSENTIAL FILE LOCATIONS**

### **Key Backend Files**
- `app/utils/temperature.py` - **Unified temperature calculation**
- `app/services/bot_evaluator.py` - Signal aggregation engine with automated trading
- `app/api/bots.py` - Primary bot management API
- `app/models/models.py` - Database schema (Bot, BotSignalHistory, Trade)
- `app/services/coinbase_service.py` - External API integration
- `app/services/trading_service.py` - Trade execution service with safety integration
- `app/services/trading_safety.py` - Trading safety validation service
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
./scripts/test.sh              # Run all 82 tests
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
- **Live API Testing**: No mocking, uses real Coinbase API
- **Automatic Cleanup**: Test bots removed after each run
- **Performance**: <8 seconds for full 82-test suite
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

## 🚀 **CURRENT PHASE - PHASE 4.3: Trading Visibility Enhancement**

### **Phase 4.3: Trading Visibility & Dashboard Enhancement (ACTIVE)**
- **Immediate Priority**: Dashboard lacks visibility into continuous trading process
- **Core Need**: Users cannot see when BUY/SELL actions are about to trigger
- **Missing Elements**: Confirmation timers, recent activity feed, trade readiness indicators
- **Current Sub-phase**: 4.3.1 - Enhanced Bot Status Display

### **Complete Infrastructure from Previous Phases**
- ✅ **Continuous Trading Operational** (Phase 4.2.1) - 2,530 trades, 99.6% success
- ✅ **Real-time bot evaluation** with polling architecture  
- ✅ **Temperature system** for trade signal strength
- ✅ **Signal confirmation** with timer data available via API
- ✅ **Trading safety** with comprehensive limits and controls
- ✅ **Live market data** integration operational

### **Phase 4.3 Immediate Objectives**
- **Trading Intent Display**: Clear BUY/SELL/HOLD indicators based on current signals
- **Confirmation Timers**: Live countdown when signals are in confirmation period
- **Activity Feed**: Recent trades, signal events, status changes in dashboard
- **Enhanced Bot Cards**: Signal strength meters, trade readiness badges, last trade info
- **Real-Time Updates**: All trading visibility data refreshes with existing 5-second polling

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

- **[Implementation Guide](../docs/IMPLEMENTATION_GUIDE.md)** - Technical patterns, code specifics
- **[Troubleshooting Playbook](../docs/TROUBLESHOOTING_PLAYBOOK.md)** - Debug solutions  
- **[Phase History](../docs/PHASE_HISTORY.md)** - Complete development timeline
- **[Phase 4 Breakdown](../docs/PHASE_4_BREAKDOWN.md)** - Current phase detailed implementation plan
- **[Project Status](../PROJECT_STATUS.md)** - Current state and next phase readiness

---
*AI Agent Instructions - Essential Guide*  
*Last Updated: September 4, 2025*  
*Phase 4.2.1 Complete → Continuous Trading Operational*
