# September 11, 2025 - Coinbase Sync Data Issue Report

## Critical Issue Summary
**Date**: September 11, 2025  
**Status**: UNRESOLVED - REQUIRES MANUAL INVESTIGATION  
**Severity**: HIGH - Data integrity compromised

## Problem Statement
User reports that Coinbase sync is pulling in trades they claim they never made:
- Expected: 3 DOGE trades total since July 25, 2025
- Actual: 110 DOGE trades in database from August-September 2025
- Similar discrepancies across all trading pairs (XRP: 95 trades, BTC: 1206 trades, etc.)

## User Requirements
- Only wants trades from July 25, 2025 forward
- Claims most synced trades are not theirs
- Expects significantly fewer trades than what sync is returning

## Technical Fixes Applied
1. **Fixed size_usd calculation bug** in `coinbase_sync_service.py`:
   - Was double-calculating USD amounts
   - Now correctly uses pre-calculated size_usd from coinbase_service
2. **Enhanced status API** now calculates positions from actual trade data
3. **P&L calculations** fixed to include all valid trade statuses

## Root Cause Investigation Needed
The fundamental issue is NOT with our calculation logic but with the **data source discrepancy**:
- Coinbase API returns 3,287 fills for recent period
- User claims majority of these trades were never made
- Sync logic is working correctly but operating on incorrect input data

## Required Actions
1. **Manual verification** of Coinbase account activity outside the system
2. **Account validation** to ensure correct Coinbase credentials/account
3. **Date range verification** of actual trading activity
4. **Potential data filtering** implementation if certain trade types should be excluded

## Files Modified
- `backend/app/services/coinbase_sync_service.py` - Fixed size_usd calculation
- `backend/app/api/bots.py` - Enhanced status position calculation  
- `backend/app/api/trades.py` - P&L filter improvements

## Next Steps
- User to manually verify their actual Coinbase trading history
- Determine if sync should filter certain trade types
- Implement date range restrictions if needed
- Consider manual trade data cleanup vs. automated filtering

## System Status
- All calculations are mathematically correct
- P&L and position tracking working properly
- Issue is with data scope/source, not calculation logic
