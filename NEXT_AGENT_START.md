# 🚀 Quick Start Guide for Next Agent

**CRITICAL**: Read this first before starting Phase 2 implementation.

## ⚡ **IMMEDIATE VERIFICATION COMMANDS**

```bash
# 1. Check service status (should all be ✅)
./scripts/status.sh

# 2. Verify all tests pass (should be 53/53)
cd backend && source venv/bin/activate && python -m pytest tests/ -q

# 3. Check current bot configuration
curl -s http://localhost:8000/api/v1/bots/ | python3 -m json.tool

# 4. View current class structure
cat docs/current_class_diagram.md
```

## 📋 **PHASE 1 COMPLETION CHECKLIST**

- ✅ **Bot-Centric Architecture**: Complete migration
- ✅ **Enhanced Parameters**: trade_step_pct, cooldown_minutes, position_size_usd
- ✅ **Signal Configuration**: JSON-based with weight validation  
- ✅ **CRUD API**: Full bot lifecycle management
- ✅ **Test Suite**: 53/53 passing with comprehensive coverage
- ✅ **Database Schema**: All new columns present and validated

## 🎯 **PHASE 2 STARTING POINT**

### **Ready to Implement**
**Phase 2: Signal Evaluation Engine** - Build real-time signal processing on the solid Phase 1 foundation.

### **Key Phase 2 Milestones**
1. **Individual Signal Calculators** - Rebuild signals to return scores (-1 to 1)
2. **Signal Aggregation Logic** - Weighted scoring for bot decisions
3. **Signal Confirmation System** - Time-based confirmation before trading

### **Available Foundation**
- **4 Configured Bots** with complete parameter sets
- **Signal Factory Pattern** ready for enhancement
- **Weight Validation System** operational
- **Comprehensive Test Suite** for regression testing

## 🔧 **ESSENTIAL FILE LOCATIONS**

### **Core Implementation Files**
```
backend/app/models/models.py          # Bot data model (enhanced)
backend/app/api/bots.py              # Bot CRUD endpoints
backend/app/services/signals/        # Signal implementations
backend/app/api/schemas.py           # Validation schemas
```

### **Key Test Files**
```
tests/test_bots.py                   # Bot CRUD & validation (21 tests)
tests/test_new_parameters.py         # New parameter testing (8 tests)
tests/test_signals.py               # Signal processing (8 tests)
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
- `/api/v1/market/` - Market data & Coinbase integration
- `/api/v1/trades/` - Trade execution endpoints

## 🚨 **IMPORTANT NOTES**

1. **All Services Running**: Don't restart unless necessary
2. **Tests Passing**: 53/53 - maintain this standard
3. **Bot-Centric**: No more signal-based references
4. **Live API Testing**: Use real Coinbase endpoints
5. **Parameter Validation**: Weight totals ≤ 1.0 enforced

## 📚 **DOCUMENTATION REFERENCES**

- **Complete Instructions**: `.github/copilot-instructions.md`
- **Current Classes**: `docs/current_class_diagram.md` 
- **Handoff Status**: `HANDOFF_STATUS.md`
- **Visual Architecture**: `docs/VISUAL_ARCHITECTURE.md`

---
**Start Here**: Phase 2 implementation ready to begin! 🚀
