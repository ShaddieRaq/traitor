# Trading System Decommission Documentation
**Date**: September 11, 2025  
**Status**: SYSTEM DECOMMISSIONED DUE TO DATA INTEGRITY ISSUES

## Decommission Reason
Critical data integrity issue identified where Coinbase sync appears to be importing trades that the user claims they never made. System suspended until manual verification and resolution.

## Final System State
- **Technical Issues**: All calculation bugs fixed (size_usd, P&L, positions)
- **Core Problem**: Data source discrepancy - sync importing unverified trades
- **User Requirement**: Only 3 DOGE trades expected, system shows 110
- **Resolution Needed**: Manual Coinbase account verification required

## Key Files and Their Current State

### Backend Services
- `backend/app/services/coinbase_sync_service.py` - ✅ Fixed size_usd calculation bug
- `backend/app/services/trading_service.py` - ✅ Fixed size field storage bug  
- `backend/app/api/bots.py` - ✅ Enhanced status with real position calculation
- `backend/app/api/trades.py` - ✅ Fixed P&L filters

### Scripts
- `scripts/wipe_and_resync.py` - Available for data cleanup
- `scripts/status.sh` - System health monitoring
- `scripts/test.sh` - Test suite validation

### Database
- Contains 3000+ trades from Coinbase sync
- User disputes most of these trades
- Requires manual verification vs actual Coinbase account activity

## Manual Resolution Required
1. Verify actual Coinbase trading history outside this system
2. Determine which trades are legitimate vs system artifacts
3. Implement proper data filtering/validation
4. Consider fresh sync with validated parameters

## System Shutdown Procedure
```bash
cd /Users/lazy_genius/Projects/trader
./scripts/stop.sh
```

## If Reactivating System
1. Resolve data source discrepancy first
2. Validate Coinbase account integration
3. Implement proper trade filtering
4. Run comprehensive validation before live trading

**CRITICAL**: Do not resume live trading until data integrity is verified
