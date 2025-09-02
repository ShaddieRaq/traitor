# 🚀 Quick Start Guide for Next Agent

**CRITICAL**: Read this first before starting Phase 2.3 implementation.

## ⚡ **IMMEDIATE VERIFICATION COMMANDS**

```bash
# 1. Check service status (should all be ✅)
./scripts/status.sh

# 2. Verify all tests pass (should be 77/77)
cd backend && source venv/bin/activate && python -m pytest tests/ -q

# 3. Check current bot configuration (5 bots)
curl -s http://localhost:8000/api/v1/bots/ | python3 -m json.tool

# 4. Test Phase 2.2 signal evaluation
curl -s "http://localhost:8000/api/v1/market/ticker/BTC-USD" | python3 -m json.tool

# 5. View current class structure (includes BotSignalEvaluator)
cat docs/current_class_diagram.md
```

## 📋 **PHASE 2.2 COMPLETION CHECKLIST**

- ✅ **Signal Evaluation Engine**: BotSignalEvaluator service operational
- ✅ **Enhanced Signal Processing**: RSI, MA, MACD with -1 to +1 scoring
- ✅ **Weighted Aggregation**: Multi-signal combination with configurable weights  
- ✅ **API Integration**: Bot evaluation endpoints functional
- ✅ **Pydantic V2 Migration**: Modern validation throughout codebase
- ✅ **Test Suite**: 77/77 passing (44% increase in coverage)
- ✅ **Code Cleanup**: Deprecated files removed, TODO comments updated

## 🎯 **PHASE 2.3 STARTING POINT**

### **Ready to Implement**
**Phase 2.3: Signal Confirmation System** - Build time-based signal verification on the completed Phase 2.2 signal evaluation engine.

### **Key Phase 2.3 Milestones**
1. **Signal Confirmation Logic** - Time-based signal verification system
2. **Confirmation Tracking** - Historical signal consistency monitoring using BotSignalHistory
3. **Trade Decision Engine** - Integration with confirmation for actual trading decisions

### **Phase 2.2 Foundation Available**
- **5 Configured Bots** with complete signal evaluation capabilities
- **BotSignalEvaluator Service** providing weighted signal aggregation
- **Enhanced Signal Classes** with precise -1 to +1 scoring
- **Comprehensive Test Suite** with Phase 2.2 signal processing coverage

## 🔧 **ESSENTIAL FILE LOCATIONS**

### **Core Implementation Files (Updated Phase 2.2)**
```
backend/app/services/bot_evaluator.py    # NEW: BotSignalEvaluator service
backend/app/services/signals/technical.py # Enhanced signal implementations  
backend/app/api/bot_evaluation.py        # NEW: Bot evaluation endpoints
backend/app/models/models.py              # Bot and BotSignalHistory models
backend/app/api/bots.py              # Bot CRUD endpoints
backend/app/services/signals/        # Signal implementations
backend/app/api/schemas.py               # Pydantic V2 validation schemas
```

### **Key Test Files (Updated Phase 2.2)**
```
tests/test_bot_evaluator.py          # NEW: BotSignalEvaluator testing (11 tests)
tests/test_signals.py               # Enhanced signal testing (21 tests)
tests/test_bots.py                   # Bot CRUD & validation (21 tests)
tests/test_new_parameters.py         # New parameter testing (8 tests)
```

## ⚠️ **CRITICAL PATTERNS TO FOLLOW**

### **Always Verify Before Coding**
```bash
# Check what exists before referencing
grep -r "class.*Signal" backend/app/services/signals/
grep -r "@router\." backend/app/api/
python scripts/generate_class_diagram.py
```

### **Use Management Scripts**
```bash
./scripts/start.sh      # Never start services manually
./scripts/status.sh     # Always check health first  
./scripts/test.sh       # Run tests after changes
```

### **API Endpoints (VERIFIED WORKING)**
- `/api/v1/bots/` - Primary bot management
- `/api/v1/bot-evaluation/` - **NEW**: Signal evaluation endpoints
- `/api/v1/market/` - Market data & Coinbase integration
- `/api/v1/trades/` - Trade execution endpoints

## 🚨 **IMPORTANT NOTES**

1. **All Services Running**: Don't restart unless necessary
2. **Tests Passing**: 77/77 - maintain this standard  
3. **Phase 2.2 Complete**: BotSignalEvaluator service operational
4. **Live API Testing**: Use real Coinbase endpoints
5. **Signal Scoring**: -1 to +1 range with precise decimal output
6. **Pydantic V2**: Modern validation patterns throughout

## 📚 **DOCUMENTATION REFERENCES**

- **Complete Instructions**: `.github/copilot-instructions.md` (Updated for Phase 2.2)
- **Current Classes**: `docs/current_class_diagram.md` 
- **Handoff Status**: `HANDOFF_STATUS.md`
- **Visual Architecture**: `docs/VISUAL_ARCHITECTURE.md`

---
**Start Here**: Phase 2 implementation ready to begin! 🚀
