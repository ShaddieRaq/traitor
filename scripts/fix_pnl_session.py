#!/usr/bin/env python3
"""
Fix P&L calculation by filtering to actual $600 trading session
"""
import sys
import os
sys.path.append('backend')

from app.core.database import SessionLocal
from app.models.models import Trade
from datetime import datetime, timedelta
from collections import defaultdict

def analyze_trading_sessions():
    """Find the correct trading session that matches $600 deposit"""
    db = SessionLocal()
    
    all_trades = db.query(Trade).filter(
        Trade.order_id.isnot(None),
        Trade.order_id != ''
    ).order_by(Trade.created_at).all()
    
    print("=== FINDING YOUR $600 TRADING SESSION ===")
    print(f"Total trades in database: {len(all_trades)}")
    
    # Strategy: Find a date range where cumulative BUY volume ≈ $600
    print("\nLooking for date range where BUY volume ≈ $600...")
    
    # Try different start dates
    potential_starts = [
        datetime(2025, 8, 1),   # August 1
        datetime(2025, 8, 15),  # Mid August  
        datetime(2025, 9, 1),   # September 1
        datetime(2025, 9, 5),   # September 5
    ]
    
    for start_date in potential_starts:
        session_trades = [t for t in all_trades if t.created_at >= start_date]
        buy_vol = sum(t.size_usd for t in session_trades if t.side == 'BUY' and t.size_usd)
        sell_vol = sum(t.size_usd for t in session_trades if t.side == 'SELL' and t.size_usd)
        
        print(f"\nFrom {start_date.strftime('%Y-%m-%d')}:")
        print(f"  Trades: {len(session_trades)}")
        print(f"  BUY volume: ${buy_vol:.2f}")
        print(f"  SELL volume: ${sell_vol:.2f}")
        print(f"  Net: ${sell_vol - buy_vol:.2f}")
        
        if 500 <= buy_vol <= 800:  # Close to $600
            print(f"  ⭐ THIS LOOKS LIKE YOUR $600 SESSION!")
            return start_date, session_trades
    
    # If no exact match, ask user
    print(f"\nCouldn't auto-detect your $600 session.")
    print(f"Please tell me: When did you make your $600 deposit?")
    print(f"Format: YYYY-MM-DD (e.g., 2025-09-01)")
    
    db.close()
    return None, []

def fix_pnl_calculation(session_start_date):
    """Update P&L to only include trades from the correct session"""
    print(f"\n=== FIXING P&L CALCULATION ===")
    print(f"Using session start date: {session_start_date}")
    
    # This would update the P&L endpoint to filter trades
    print(f"Next step: Update backend/app/api/trades.py to filter trades >= {session_start_date}")
    print(f"This will make P&L calculation only include YOUR $600 session trades.")

if __name__ == "__main__":
    start_date, session_trades = analyze_trading_sessions()
    if start_date:
        fix_pnl_calculation(start_date)
