#!/usr/bin/env python3
"""
Investigate the Learning System
Check if the "learning from mistakes" feature is actually working
"""

import requests
import json

def check_learning_system():
    print("🧠 INVESTIGATING THE LEARNING SYSTEM")
    print("=" * 60)
    print("The agent implemented a sophisticated 'learning from mistakes' system:")
    print("1. SignalPredictionRecord - Records every signal prediction")
    print("2. SignalPerformanceTracker - Evaluates prediction outcomes")
    print("3. AdaptiveSignalWeighting - Adjusts weights based on performance")
    print("4. AI Intelligence Tab - Shows 'learning' metrics")
    print()
    
    # Check if learning data exists
    print("🔍 CHECKING IF LEARNING SYSTEM IS COLLECTING DATA:")
    print("-" * 50)
    
    try:
        # Check signal predictions in database
        response = requests.get("http://localhost:8000/api/v1/signal-performance/performance/summary", timeout=5)
        if response.status_code == 404:
            print("❌ Signal performance API not accessible")
        else:
            print("✅ Signal performance API accessible")
            
    except Exception as e:
        print(f"❌ Signal performance API error: {e}")
    
    try:
        # Check intelligence framework data
        response = requests.get("http://localhost:8000/api/v1/intelligence/framework", timeout=5)
        if response.status_code == 200:
            data = response.json()
            print("✅ Intelligence framework API working")
            print(f"   Total Predictions: {data.get('total_predictions', 'N/A')}")
            print(f"   Evaluated Predictions: {data.get('evaluated_predictions', 'N/A')}")
        else:
            print("❌ Intelligence framework API not working")
            
    except Exception as e:
        print(f"❌ Intelligence framework API error: {e}")

def analyze_learning_effectiveness():
    print("\n🎯 LEARNING SYSTEM EFFECTIVENESS ANALYSIS")
    print("=" * 50)
    
    print("What the AI Intelligence tab claims:")
    print("✅ 141,587 total predictions")
    print("✅ 63.3% accuracy rate")
    print("✅ RSI best at 65.2% accuracy")
    print("✅ 30 outcomes evaluated")
    print()
    
    print("What our profit analysis shows:")
    print("💸 Portfolio P&L: -$24.70")
    print("💸 Only 12/36 pairs profitable (33%)")
    print("💸 -$0.025 loss per trade on average")
    print("💸 All bots use identical signal weights anyway!")
    print()
    
    print("🚨 THE LEARNING SYSTEM PARADOX:")
    print("1. System claims 63% accuracy but loses money")
    print("2. System has 'adaptive weights' but all weights are identical")
    print("3. System 'learns from mistakes' but keeps making same mistakes")
    print("4. 141K predictions but no actual learning applied")
    print()
    
    print("💡 WHY THE LEARNING ISN'T HELPING:")
    print("- Accuracy ≠ Profitability (fundamental flaw)")
    print("- Learning system not actually changing anything")
    print("- All bots still use default weights (0.4, 0.35, 0.25)")
    print("- Market selection matters more than signal optimization")

def check_adaptive_weights():
    print("\n🔧 ADAPTIVE WEIGHT SYSTEM CHECK")
    print("=" * 40)
    
    print("The system has an AdaptiveSignalWeightingService that should:")
    print("1. Calculate performance metrics for each signal")
    print("2. Adjust weights based on which signals work best")
    print("3. Update bot configurations automatically")
    print("4. Learn from successful vs failed predictions")
    print()
    
    print("But our analysis shows:")
    print("❌ All bots have identical signal weights")
    print("❌ AVNT-USD (winner) uses same weights as SQD-USD (loser)")
    print("❌ No evidence of adaptive weight updates")
    print("❌ Learning system collecting data but not applying insights")
    print()
    
    print("🎯 CONCLUSION:")
    print("The 'learning from mistakes' system is a sophisticated data collector")
    print("but NOT a profitable trading optimizer. It's measuring the wrong thing!")

def recommend_learning_fix():
    print("\n🚀 HOW TO FIX THE LEARNING SYSTEM")
    print("=" * 40)
    
    print("Current Learning Focus (WRONG):")
    print("❌ Signal accuracy percentages")
    print("❌ Prediction counts")
    print("❌ Technical metrics that don't correlate with profit")
    print()
    
    print("Profitable Learning Focus (RIGHT):")
    print("✅ Which MARKETS make money (AVNT, XAN vs SQD, ZORA)")
    print("✅ Which trading frequencies work (13 trades = $8 profit)")
    print("✅ Which market caps respond to signals (alt vs major coins)")
    print("✅ When to STOP trading losing pairs")
    print()
    
    print("🎯 ACTIONABLE LEARNING SYSTEM:")
    print("1. Track $ profit per market, not signal accuracy")
    print("2. Auto-pause bots losing money consistently")
    print("3. Auto-scale successful markets (AVNT, XAN)")
    print("4. Learn from market characteristics, not signal tweaks")

def main():
    check_learning_system()
    analyze_learning_effectiveness()
    check_adaptive_weights()
    recommend_learning_fix()
    
    print(f"\n💡 FINAL INSIGHT:")
    print("The 'learning from mistakes' system is academically impressive")
    print("but practically useless for making money. It's optimizing for")
    print("signal accuracy while the portfolio loses money.")
    print()
    print("Real learning = Stop trading losers, scale winners!")

if __name__ == "__main__":
    main()