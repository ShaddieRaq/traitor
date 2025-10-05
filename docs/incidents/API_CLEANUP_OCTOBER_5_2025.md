# API Cleanup - October 5, 2025

## Summary
Removed deprecated `/api/v1/trades/` endpoints that were returning 410 errors and cluttering the API.

## Endpoints Removed
- `GET /api/v1/trades/` - Was deprecated due to data corruption
- `GET /api/v1/trades/stats` - Was deprecated due to data corruption  
- `GET /api/v1/trades/performance/by-product` - Was deprecated due to massive data corruption

## Replacement Endpoints (Use These)
- `GET /api/v1/raw-trades/` - Clean Coinbase trade data
- `GET /api/v1/raw-trades/stats` - Accurate trade statistics
- `GET /api/v1/raw-trades/pnl-by-product` - Clean P&L data by trading pair

## Impact
- Cleaner API with no confusing error responses
- All functionality preserved in the clean endpoints
- Frontend should use only the `/api/v1/raw-trades/` endpoints

## Updated Documentation
- Updated `.github/copilot-instructions.md` with endpoint removal notice
- Updated `README.md` Tech Stack section
- Noted in all relevant documentation that deprecated endpoints are completely removed