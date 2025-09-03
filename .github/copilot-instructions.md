# Bot-Centric Coinbase Trading System - AI Agent Guide

## 🚀 **IMMEDIATE PRODUCTIVITY ESSENTIALS**

### **Critical First Commands**
```bash
./scripts/status.sh   # Check if system is running (all should be ✅)
./scripts/start.sh    # Start all services if needed
curl -s http://localhost:8000/api/v1/bots/status/summary | python3 -m json.tool  # View live bot status
```

### **Current System Status (September 3, 2025)**
- ✅ **Phase 3.3 Complete**: Real-time polling architecture operational  
- ✅ **2 Production Bots**: BTC Scalper (HOT 🔥), ETH Momentum (WARM 🌡️)
- ✅ **104/104 tests passing** (100% success rate)
- ✅ **Live UI Updates**: Values update every 5 seconds without refresh
- ✅ **Fresh Data Pipeline**: Backend performs live evaluations on each request
- ✅ **Clean Production State**: No test artifacts, unified temperature system

## 🎯 **ARCHITECTURE ESSENTIALS**

### **Bot-Centric Design**
- **One bot per trading pair** with weighted signal aggregation
- **Signal scoring**: -1 (strong sell) to +1 (strong buy)
- **Temperature indicators**: HOT 🔥/WARM 🌡️/COOL ❄️/FROZEN 🧊
- **Weight validation**: Signal weights must be ≤ 1.0 (API enforced)

### **Real-Time Data Flow**
- **Frontend**: TanStack Query polling every 5 seconds
- **Backend**: Fresh market evaluation on each API request  
- **Temperature calculation**: Unified source in `app/utils/temperature.py`
- **UI updates**: Automatic without manual refresh

### **Service Architecture**
```
Backend: FastAPI + SQLAlchemy + Celery + Redis
Database: SQLite with Bot/BotSignalHistory models  
Frontend: React 18 + TypeScript + TailwindCSS + TanStack Query
Trading: Coinbase Advanced Trade API (JWT auth)
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

# Expected results (Sept 3, 2025):
# BTC Scalper: HOT 🔥 (score: ~0.522)
# ETH Momentum: WARM 🌡️ (score: ~0.064)

# Verify UI auto-updates
open http://localhost:3000  # Values should change every 5 seconds

# Test signal evaluation
curl -X POST http://localhost:8000/api/v1/bot-evaluation/1/evaluate
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

## ⚠️ **CRITICAL LESSONS LEARNED**

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
- `app/services/bot_evaluator.py` - Signal aggregation engine  
- `app/api/bots.py` - Primary bot management API
- `app/models/models.py` - Database schema (Bot, BotSignalHistory)
- `app/services/coinbase_service.py` - External API integration

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
./scripts/test.sh              # Run all 104 tests
./scripts/test.sh --unit       # Signal processing only  
./scripts/test.sh --integration # API and database tests
```

### **Test Coverage Areas**
- **Bot CRUD Operations**: 21 tests (creation, validation, parameters)
- **Signal Processing**: 21 tests (RSI, MA, MACD calculations)
- **Confirmation System**: 64 tests (time-based signal validation)
- **Temperature System**: 15 tests (unified calculation, thresholds)
- **Live API Integration**: 7 tests (real Coinbase endpoints)

### **Test Quality Principles**
- **Live API Testing**: No mocking, uses real Coinbase API
- **Automatic Cleanup**: Test bots removed after each run
- **Performance**: <4 seconds for full 104-test suite
- **Real Data**: Tests use actual market conditions

## 🚀 **NEXT PHASE READINESS - PHASE 4**

### **Ready Infrastructure**
- ✅ **Real-time bot evaluation** with polling architecture
- ✅ **Temperature system** for trade signal strength
- ✅ **Signal confirmation** preventing false signals
- ✅ **Clean codebase** with comprehensive test coverage
- ✅ **Live market data** integration operational

### **Phase 4 Objectives**
- **Paper Trading**: Simulate trades using existing signal evaluation
- **Position Tracking**: Monitor current positions with P&L calculation
- **Risk Management**: Automated stop-loss using temperature system
- **Order Execution**: Integration with Coinbase order placement

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

- **[Implementation Guide](docs/IMPLEMENTATION_GUIDE.md)** - Technical patterns, code specifics
- **[Troubleshooting Playbook](docs/TROUBLESHOOTING_PLAYBOOK.md)** - Debug solutions  
- **[Phase History](docs/PHASE_HISTORY.md)** - Complete development timeline
- **[Project Status](PROJECT_STATUS.md)** - Current state and next phase readiness

---
*AI Agent Instructions - Essential Guide*  
*Last Updated: September 3, 2025*  
*Phase 3.3 Complete → Phase 4 Ready*
