# Codebase Cleanup Plan - September 2025

## Cleanup Categories

### 1. Database Backup Files (SAFE TO REMOVE)
- `backend/trader_backup_20250906_*.db` (multiple files from Sept 6)
- `backend/trader_backup_20250907_105340.db` 
- `backend/trader_backup_20250911_*.db` (multiple files from Sept 11)
- `backend/trader_backup_migration_20250913_123112.db`

**Action**: Keep only the most recent backup, remove old ones.

### 2. Legacy Analysis Scripts (MOVE TO ARCHIVE)
- `show_all_signals.py` - Used for signal validation, keep as reference
- `test_full_pnl_fix.py` - Historical P&L fix validation
- `validate_pnl.py` - P&L validation utilities
- `backend/analyze_data_integrity.py` - Data corruption analysis
- `backend/calculate_pnl_by_pair.py` - P&L calculation helpers
- `backend/complete_raw_trades_migration.py` - Migration script
- `backend/create_raw_trades_table.py` - Table creation script
- `backend/eliminate_trades_table.py` - Table elimination script
- `backend/fix_commission_data.py` - Commission data fix
- `backend/simplified_bot_demo.py` - Demo script
- `backend/sync_raw_coinbase.py` - Raw sync script
- `backend/sync_raw_trades.py` - Trade sync script

**Action**: Move to `docs/legacy_scripts/` directory for reference.

### 3. Configuration Files (CONSOLIDATE)
- `optimal_bot_configuration.json` - Seems redundant
- `optimized_bot_config.json` - Seems redundant

**Action**: Consolidate or move to examples directory.

### 4. Database Files (ORGANIZE)
- `trader.db` in root - Should be in backend only
- `backend/trader.db` - Primary database

**Action**: Ensure single source of truth.

### 5. Documentation (UPDATE NEEDED)
- All files in `docs/` directory need review for currency
- `.github/copilot-instructions.md` needs update with recent changes

## Execution Order
1. Create archive directories
2. Move legacy scripts
3. Clean up old database backups
4. Consolidate configuration files
5. Update all documentation
6. Update copilot instructions
