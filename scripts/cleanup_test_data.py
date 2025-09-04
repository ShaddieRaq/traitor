#!/usr/bin/env python3
"""
Test Data Cleanup Script
========================

This script cleans up test data that accumulates after running the test suite.
It removes:
- All bots with 'test' in their name
- Associated trades and signal history for test bots
- Orphaned signal history entries (where bot no longer exists)
- Old signal history entries (older than 24 hours) to prevent accumulation

Usage:
    python scripts/cleanup_test_data.py [--dry-run] [--keep-hours=24]

Options:
    --dry-run       Show what would be deleted without actually deleting
    --keep-hours    Number of hours of signal history to keep (default: 24)
"""

import sys
import os
from datetime import datetime, timedelta
import argparse

# Add the backend directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'backend'))

from app.core.database import SessionLocal
from app.models.models import Bot, Trade, BotSignalHistory


def cleanup_test_data(dry_run=False, keep_hours=24):
    """Clean up test data from the database."""
    db = SessionLocal()
    
    try:
        print('🧹 Trading Bot Test Data Cleanup')
        print('=' * 50)
        
        if dry_run:
            print('🔍 DRY RUN MODE - No changes will be made')
            print()
        
        # Step 1: Find test bots
        test_bots = db.query(Bot).filter(
            Bot.name.like('%test%') | 
            Bot.name.like('%Test%') | 
            Bot.name.like('%unittest%')
        ).all()
        
        print(f'📋 Found {len(test_bots)} test bots:')
        for bot in test_bots:
            print(f'  - {bot.name} (ID: {bot.id}, Status: {bot.status})')
        
        if test_bots:
            test_bot_ids = [bot.id for bot in test_bots]
            
            # Count related data
            signal_count = db.query(BotSignalHistory).filter(BotSignalHistory.bot_id.in_(test_bot_ids)).count()
            trade_count = db.query(Trade).filter(Trade.bot_id.in_(test_bot_ids)).count()
            
            print(f'📊 Associated data:')
            print(f'  - Signal history entries: {signal_count}')
            print(f'  - Trade entries: {trade_count}')
            
            if not dry_run:
                print()
                print('🗑️  Deleting test bot data...')
                
                # Delete signal history
                if signal_count > 0:
                    db.query(BotSignalHistory).filter(BotSignalHistory.bot_id.in_(test_bot_ids)).delete(synchronize_session=False)
                    print(f'  ✅ Deleted {signal_count} signal history entries')
                
                # Delete trades
                if trade_count > 0:
                    db.query(Trade).filter(Trade.bot_id.in_(test_bot_ids)).delete(synchronize_session=False)
                    print(f'  ✅ Deleted {trade_count} trade entries')
                
                # Delete bots
                for bot in test_bots:
                    db.delete(bot)
                print(f'  ✅ Deleted {len(test_bots)} test bots')
        
        # Step 2: Clean up orphaned data
        print()
        print('🔍 Checking for orphaned data...')
        
        valid_bot_ids = [bot.id for bot in db.query(Bot).all()]
        
        # Find orphaned signal history
        orphaned_signals = db.query(BotSignalHistory).filter(
            (BotSignalHistory.bot_id.is_(None)) | 
            (~BotSignalHistory.bot_id.in_(valid_bot_ids))
        ).count()
        
        # Find orphaned trades
        orphaned_trades = db.query(Trade).filter(
            (Trade.bot_id.is_(None)) | 
            (~Trade.bot_id.in_(valid_bot_ids))
        ).count()
        
        print(f'📊 Orphaned data found:')
        print(f'  - Orphaned signal history: {orphaned_signals}')
        print(f'  - Orphaned trades: {orphaned_trades}')
        
        if not dry_run and (orphaned_signals > 0 or orphaned_trades > 0):
            print()
            print('🗑️  Cleaning up orphaned data...')
            
            if orphaned_signals > 0:
                db.query(BotSignalHistory).filter(
                    (BotSignalHistory.bot_id.is_(None)) | 
                    (~BotSignalHistory.bot_id.in_(valid_bot_ids))
                ).delete(synchronize_session=False)
                print(f'  ✅ Deleted {orphaned_signals} orphaned signal entries')
            
            if orphaned_trades > 0:
                db.query(Trade).filter(
                    (Trade.bot_id.is_(None)) | 
                    (~Trade.bot_id.in_(valid_bot_ids))
                ).delete(synchronize_session=False)
                print(f'  ✅ Deleted {orphaned_trades} orphaned trades')
        
        # Step 3: Clean up old signal history
        print()
        print(f'🗑️  Cleaning up signal history older than {keep_hours} hours...')
        
        cutoff_time = datetime.utcnow() - timedelta(hours=keep_hours)
        old_signals_count = 0
        
        for bot in db.query(Bot).all():
            old_signals = db.query(BotSignalHistory).filter(
                BotSignalHistory.bot_id == bot.id,
                BotSignalHistory.timestamp < cutoff_time
            ).count()
            
            if old_signals > 0:
                print(f'  - {bot.name}: {old_signals} old entries')
                old_signals_count += old_signals
                
                if not dry_run:
                    db.query(BotSignalHistory).filter(
                        BotSignalHistory.bot_id == bot.id,
                        BotSignalHistory.timestamp < cutoff_time
                    ).delete(synchronize_session=False)
        
        if old_signals_count > 0:
            if not dry_run:
                print(f'  ✅ Deleted {old_signals_count} old signal entries')
        else:
            print('✅ No old signal history to clean up')
        
        # Step 4: Clean up Python cache files
        print()
        print('🧹 Cleaning up Python cache files...')
        import subprocess
        import os
        
        project_root = os.path.dirname(os.path.dirname(__file__))
        
        try:
            # Remove __pycache__ directories
            result = subprocess.run(['find', project_root, '-type', 'd', '-name', '__pycache__', '-exec', 'rm', '-rf', '{}', '+'], 
                                  capture_output=True, text=True, check=False)
            
            # Remove .pyc files
            result = subprocess.run(['find', project_root, '-type', 'f', '-name', '*.pyc', '-delete'], 
                                  capture_output=True, text=True, check=False)
            
            # Remove pytest cache
            result = subprocess.run(['find', project_root, '-type', 'd', '-name', '.pytest_cache', '-exec', 'rm', '-rf', '{}', '+'], 
                                  capture_output=True, text=True, check=False)
            
            print('  ✅ Python cache files cleaned up')
        except Exception as e:
            print(f'  ⚠️  Cache cleanup failed: {e}')
        
        # Commit changes
        if not dry_run:
            db.commit()
            print()
            print('💾 All changes committed to database')
        
        # Step 4: Show final state
        print()
        print('📊 Database state after cleanup:')
        print('=' * 50)
        
        final_bots = db.query(Bot).count()
        final_trades = db.query(Trade).count()
        final_signals = db.query(BotSignalHistory).count()
        
        print(f'Total bots: {final_bots}')
        print(f'Total trades: {final_trades}')
        print(f'Total signal history: {final_signals}')
        
        print()
        print('🤖 Remaining bots:')
        for bot in db.query(Bot).all():
            signal_count = db.query(BotSignalHistory).filter(BotSignalHistory.bot_id == bot.id).count()
            print(f'  - {bot.name} (ID: {bot.id}, Status: {bot.status}) - {signal_count} signals')
        
        if dry_run:
            print()
            print('🔍 DRY RUN COMPLETE - No changes were made')
            print('    Run without --dry-run to actually perform cleanup')
        else:
            print()
            print('✅ Cleanup completed successfully!')
            
    except Exception as e:
        if not dry_run:
            db.rollback()
        print(f'❌ Error during cleanup: {e}')
        raise
    finally:
        db.close()


def main():
    parser = argparse.ArgumentParser(description='Clean up test data from the trading bot database')
    parser.add_argument('--dry-run', action='store_true', 
                        help='Show what would be deleted without actually deleting')
    parser.add_argument('--keep-hours', type=int, default=24,
                        help='Number of hours of signal history to keep (default: 24)')
    
    args = parser.parse_args()
    
    cleanup_test_data(dry_run=args.dry_run, keep_hours=args.keep_hours)


if __name__ == '__main__':
    main()
