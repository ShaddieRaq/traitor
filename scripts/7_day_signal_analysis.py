#!/usr/bin/env python3
"""
7-Day Signal Performance Analysis
================================

Analyzes signal accuracy and trading performance over the last 7 days of clean data
to identify optimization opportunities for Phase A.2 - Signal Strategy Enhancement.

Focus Areas:
1. Signal-to-outcome correlation
2. Parameter sensitivity testing (±0.1 vs ±0.05 thresholds)
3. Balance constraint impact analysis
4. Market condition performance

Usage:
    python scripts/7_day_signal_analysis.py
"""

import sys
import os
import requests
import json
from datetime import datetime, timedelta
from collections import defaultdict

# Add the backend directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'backend'))

class SevenDayAnalyzer:
    def __init__(self):
        self.base_url = "http://localhost:8000/api/v1"
        self.seven_days_ago = datetime.now() - timedelta(days=7)
        self.analysis_results = {}
        
    def fetch_data(self, endpoint, params=None):
        """Fetch data from API with error handling."""
        try:
            response = requests.get(f"{self.base_url}{endpoint}", params=params, timeout=10)
            if response.status_code == 200:
                return response.json()
            else:
                print(f"❌ API Error {response.status_code}: {endpoint}")
                return None
        except Exception as e:
            print(f"❌ Request failed for {endpoint}: {e}")
            return None

    def get_current_bot_status(self):
        """Get current bot status and signal information."""
        print("📊 Fetching current bot status...")
        bots = self.fetch_data("/bots/status/enhanced")
        if not bots:
            return {}
            
        bot_status = {}
        for bot in bots:
            bot_status[bot['pair']] = {
                'id': bot['id'],
                'name': bot['name'],
                'status': bot['status'],
                'current_score': bot['current_combined_score'],
                'temperature': bot['temperature'],
                'trading_intent': bot['trading_intent'],
                'trade_readiness': bot['trade_readiness'],
                'last_trade': bot.get('last_trade')
            }
        print(f"✅ Retrieved status for {len(bot_status)} bots")
        return bot_status

    def get_product_performance(self):
        """Get 7-day product performance data."""
        print("💰 Fetching product performance data...")
        performance = self.fetch_data("/raw-trades/pnl-by-product")
        if not performance or 'products' not in performance:
            return {}
            
        # Filter for products with significant activity (>10 trades)
        active_products = {}
        for product in performance['products']:
            if product['trade_count'] > 10:
                active_products[product['product_id']] = product
                
        print(f"✅ Found {len(active_products)} actively traded products")
        return active_products

    def analyze_balance_constraints(self, bot_status):
        """Analyze which bots are blocked by balance constraints."""
        print("⚖️ Analyzing balance constraints...")
        
        blocked_bots = []
        trading_bots = []
        
        for pair, bot in bot_status.items():
            readiness = bot['trade_readiness']
            if readiness['status'] == 'blocked':
                if 'insufficient_balance' in readiness.get('blocking_reason', ''):
                    blocked_bots.append({
                        'pair': pair,
                        'name': bot['name'],
                        'reason': readiness['blocking_reason'],
                        'current_score': bot['current_score'],
                        'temperature': bot['temperature']
                    })
            else:
                trading_bots.append(pair)
        
        print(f"🚫 {len(blocked_bots)} bots blocked by balance constraints")
        print(f"✅ {len(trading_bots)} bots able to trade")
        
        return {
            'blocked_count': len(blocked_bots),
            'trading_count': len(trading_bots),
            'blocked_details': blocked_bots,
            'trading_pairs': trading_bots
        }

    def analyze_signal_thresholds(self, bot_status):
        """Analyze current signal scores vs proposed threshold changes."""
        print("🎯 Analyzing signal threshold sensitivity...")
        
        current_threshold = 0.1  # Current ±0.1 threshold
        proposed_threshold = 0.05  # Proposed ±0.05 threshold
        
        threshold_analysis = {
            'current': {'buy_signals': 0, 'sell_signals': 0, 'hold_signals': 0},
            'proposed': {'buy_signals': 0, 'sell_signals': 0, 'hold_signals': 0},
            'changes': []
        }
        
        for pair, bot in bot_status.items():
            score = bot['current_score']
            
            # Current threshold logic
            current_action = 'hold'
            if score >= current_threshold:
                current_action = 'buy'
                threshold_analysis['current']['buy_signals'] += 1
            elif score <= -current_threshold:
                current_action = 'sell'
                threshold_analysis['current']['sell_signals'] += 1
            else:
                threshold_analysis['current']['hold_signals'] += 1
            
            # Proposed threshold logic
            proposed_action = 'hold'
            if score >= proposed_threshold:
                proposed_action = 'buy'
                threshold_analysis['proposed']['buy_signals'] += 1
            elif score <= -proposed_threshold:
                proposed_action = 'sell'
                threshold_analysis['proposed']['sell_signals'] += 1
            else:
                threshold_analysis['proposed']['hold_signals'] += 1
            
            # Track changes
            if current_action != proposed_action:
                threshold_analysis['changes'].append({
                    'pair': pair,
                    'score': score,
                    'current_action': current_action,
                    'proposed_action': proposed_action,
                    'temperature': bot['temperature']
                })
        
        print(f"📈 Threshold change would affect {len(threshold_analysis['changes'])} bots")
        return threshold_analysis

    def analyze_profitable_patterns(self, performance_data):
        """Identify patterns in profitable vs unprofitable pairs."""
        print("💡 Analyzing profitable trading patterns...")
        
        profitable = []
        unprofitable = []
        
        for product_id, data in performance_data.items():
            pnl = data['net_pnl_usd']
            win_rate = data['sell_trades'] / data['trade_count'] if data['trade_count'] > 0 else 0
            
            analysis = {
                'pair': product_id,
                'net_pnl': pnl,
                'trade_count': data['trade_count'],
                'win_rate': win_rate,
                'buy_trades': data['buy_trades'],
                'sell_trades': data['sell_trades'],
                'avg_trade_size': data['total_spent_usd'] / data['buy_trades'] if data['buy_trades'] > 0 else 0
            }
            
            if pnl > 0:
                profitable.append(analysis)
            else:
                unprofitable.append(analysis)
        
        # Sort by profitability
        profitable.sort(key=lambda x: x['net_pnl'], reverse=True)
        unprofitable.sort(key=lambda x: x['net_pnl'])
        
        print(f"📈 {len(profitable)} profitable pairs, {len(unprofitable)} unprofitable pairs")
        
        return {
            'profitable': profitable,
            'unprofitable': unprofitable,
            'total_pnl': sum(p['net_pnl'] for p in profitable + unprofitable)
        }

    def generate_recommendations(self, balance_analysis, threshold_analysis, profitability_analysis):
        """Generate actionable recommendations based on analysis."""
        recommendations = []
        
        # Balance constraint recommendations
        if balance_analysis['blocked_count'] > 0:
            blocked_with_signals = [b for b in balance_analysis['blocked_details'] 
                                  if abs(b['current_score']) > 0.05]
            if blocked_with_signals:
                recommendations.append({
                    'type': 'balance_allocation',
                    'priority': 'HIGH',
                    'action': f"Allocate additional balance to {len(blocked_with_signals)} bots with active signals",
                    'impact': 'Enable trading on bots showing market opportunity',
                    'pairs': [b['pair'] for b in blocked_with_signals]
                })
        
        # Threshold adjustment recommendations
        if len(threshold_analysis['changes']) > 0:
            buy_increases = len([c for c in threshold_analysis['changes'] 
                               if c['proposed_action'] == 'buy'])
            if buy_increases > 0:
                recommendations.append({
                    'type': 'threshold_adjustment',
                    'priority': 'MEDIUM',
                    'action': f"Test ±0.05 threshold on {buy_increases} pairs showing additional buy opportunities",
                    'impact': 'Increase trading frequency with more sensitive signals',
                    'test_pairs': [c['pair'] for c in threshold_analysis['changes'][:3]]  # Test on 3 pairs first
                })
        
        # Profitable pair focus
        top_performers = profitability_analysis['profitable'][:3]
        if top_performers:
            recommendations.append({
                'type': 'capital_optimization',
                'priority': 'MEDIUM',
                'action': f"Increase position sizes on top performing pairs: {', '.join([p['pair'] for p in top_performers])}",
                'impact': f"Potential to scale profits from ${sum(p['net_pnl'] for p in top_performers):.2f}",
                'pairs': [p['pair'] for p in top_performers]
            })
        
        return recommendations

    def run_analysis(self):
        """Execute complete 7-day analysis."""
        print("🚀 Starting 7-Day Signal Performance Analysis")
        print("=" * 60)
        
        # Gather data
        bot_status = self.get_current_bot_status()
        performance_data = self.get_product_performance()
        
        if not bot_status or not performance_data:
            print("❌ Failed to gather required data")
            return
        
        # Perform analyses
        balance_analysis = self.analyze_balance_constraints(bot_status)
        threshold_analysis = self.analyze_signal_thresholds(bot_status)
        profitability_analysis = self.analyze_profitable_patterns(performance_data)
        
        # Generate recommendations
        recommendations = self.generate_recommendations(
            balance_analysis, threshold_analysis, profitability_analysis
        )
        
        # Store results
        self.analysis_results = {
            'timestamp': datetime.now().isoformat(),
            'analysis_period': '7_days',
            'bot_status_summary': {
                'total_bots': len(bot_status),
                'blocked_by_balance': balance_analysis['blocked_count'],
                'actively_trading': balance_analysis['trading_count']
            },
            'threshold_impact': threshold_analysis,
            'profitability_summary': {
                'profitable_pairs': len(profitability_analysis['profitable']),
                'unprofitable_pairs': len(profitability_analysis['unprofitable']),
                'total_pnl': profitability_analysis['total_pnl']
            },
            'recommendations': recommendations,
            'detailed_results': {
                'balance_analysis': balance_analysis,
                'profitability_analysis': profitability_analysis
            }
        }
        
        # Display results
        self.display_results()
        
        # Save results
        self.save_results()

    def display_results(self):
        """Display analysis results in formatted output."""
        print("\n" + "=" * 60)
        print("📊 7-DAY ANALYSIS RESULTS")
        print("=" * 60)
        
        # Bot status summary
        summary = self.analysis_results['bot_status_summary']
        print(f"\n🤖 BOT STATUS SUMMARY:")
        print(f"   Total Bots: {summary['total_bots']}")
        print(f"   Actively Trading: {summary['actively_trading']}")
        print(f"   Blocked by Balance: {summary['blocked_by_balance']}")
        
        # Profitability summary
        prof_summary = self.analysis_results['profitability_summary']
        print(f"\n💰 PROFITABILITY SUMMARY:")
        print(f"   Total P&L: ${prof_summary['total_pnl']:.2f}")
        print(f"   Profitable Pairs: {prof_summary['profitable_pairs']}")
        print(f"   Unprofitable Pairs: {prof_summary['unprofitable_pairs']}")
        
        # Top performers
        profitable = self.analysis_results['detailed_results']['profitability_analysis']['profitable']
        if profitable:
            print(f"\n📈 TOP PERFORMERS:")
            for i, pair in enumerate(profitable[:3]):
                print(f"   {i+1}. {pair['pair']}: ${pair['net_pnl']:.2f} ({pair['trade_count']} trades)")
        
        # Recommendations
        print(f"\n🎯 RECOMMENDATIONS:")
        for i, rec in enumerate(self.analysis_results['recommendations']):
            print(f"   {i+1}. [{rec['priority']}] {rec['action']}")
            print(f"      Impact: {rec['impact']}")
        
        print("\n" + "=" * 60)

    def save_results(self):
        """Save analysis results to file."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"7_day_analysis_{timestamp}.json"
        filepath = os.path.join(os.path.dirname(__file__), 'analysis', filename)
        
        # Create analysis directory if it doesn't exist
        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        
        with open(filepath, 'w') as f:
            json.dump(self.analysis_results, f, indent=2)
        
        print(f"💾 Analysis results saved to: {filepath}")

if __name__ == "__main__":
    analyzer = SevenDayAnalyzer()
    analyzer.run_analysis()
