from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.models.models import Bot, Trade
from app.services.bot_evaluator import BotSignalEvaluator
from app.services.coinbase_service import CoinbaseService
from app.services.trading_safety import TradingSafetyService
from typing import Dict, Any, List
import os
from datetime import datetime, timedelta

router = APIRouter()

@router.get("/trading-diagnosis")
async def get_trading_diagnosis(db: Session = Depends(get_db)) -> Dict[str, Any]:
    """
    Comprehensive trading diagnosis to understand why trades aren't executing
    """
    try:
        bots = db.query(Bot).all()
        evaluator = BotSignalEvaluator()
        coinbase_service = CoinbaseService()
        safety_service = TradingSafetyService()
        
        diagnosis = {
            "system_status": {},
            "bot_diagnoses": [],
            "environment": {},
            "recent_activity": [],
            "blocking_issues": []
        }
        
        # System-level diagnosis
        diagnosis["system_status"] = {
            "safety_enabled": True,
            "coinbase_connected": True,  # We'll test this
            "total_bots": len(bots),
            "running_bots": len([b for b in bots if b.status == "RUNNING"])
        }
        
        # Environment variables
        diagnosis["environment"] = {
            "coinbase_api_configured": bool(os.getenv("COINBASE_API_KEY")),
            "debug_mode": os.getenv("DEBUG", "False").lower() == "true"
        }
        
        # Safety status
        try:
            safety_status = await safety_service.get_safety_status(db)
            diagnosis["system_status"]["safety_limits"] = safety_status
        except Exception as e:
            diagnosis["blocking_issues"].append({
                "issue": "Safety Service Error",
                "description": str(e),
                "severity": "critical"
            })
        
        # Test Coinbase connection
        try:
            accounts = coinbase_service.get_accounts()
            diagnosis["system_status"]["coinbase_connected"] = len(accounts) > 0
        except Exception as e:
            diagnosis["system_status"]["coinbase_connected"] = False
            diagnosis["blocking_issues"].append({
                "issue": "Coinbase API Connection Failed",
                "description": str(e),
                "severity": "critical"
            })
        
        # Recent trades analysis
        recent_trades = db.query(Trade).filter(
            Trade.executed_at >= datetime.utcnow() - timedelta(hours=2)
        ).order_by(Trade.executed_at.desc()).limit(10).all()
        
        diagnosis["recent_activity"] = [
            {
                "bot_id": trade.bot_id,
                "side": trade.side,
                "amount": trade.amount,
                "status": trade.status,
                "executed_at": trade.executed_at.isoformat() if trade.executed_at else None,
                "minutes_ago": int((datetime.utcnow() - trade.executed_at).total_seconds() / 60) if trade.executed_at else None
            }
            for trade in recent_trades
        ]
        
        # Individual bot diagnosis
        for bot in bots:
            bot_diagnosis = {
                "bot_id": bot.id,
                "name": bot.name,
                "status": bot.status,
                "issues": [],
                "recommendations": []
            }
            
            try:
                # Get fresh market data and evaluate
                market_data = coinbase_service.get_historical_data(bot.pair)
                if market_data is None or market_data.empty:
                    bot_diagnosis["issues"].append({
                        "issue": "No Market Data",
                        "description": f"Cannot retrieve market data for {bot.pair}",
                        "severity": "critical"
                    })
                    continue
                
                # Evaluate bot signals
                evaluation = evaluator.evaluate_bot(bot, market_data)
                
                bot_diagnosis.update({
                    "signal_strength": evaluation.get("overall_score", 0),
                    "next_action": evaluation.get("action", "hold"),
                    "confirmation_active": evaluation.get("confirmation", {}).get("is_active", False),
                    "can_trade": evaluation.get("automatic_trade", {}).get("can_execute", False) if evaluation.get("automatic_trade") else False
                })
                
                # Check for specific blocking issues
                if abs(evaluation.get("overall_score", 0)) >= 0.8:  # Strong signal
                    if not evaluation.get("confirmation", {}).get("is_active", False):
                        bot_diagnosis["issues"].append({
                            "issue": "Strong Signal Not Confirming",
                            "description": f"Signal strength {abs(evaluation.get('overall_score', 0)):.1%} but confirmation not started",
                            "severity": "warning"
                        })
                    
                    if evaluation.get("confirmation", {}).get("is_active", False):
                        remaining = evaluation.get("confirmation", {}).get("time_remaining_seconds", 0)
                        if remaining <= 0:
                            bot_diagnosis["issues"].append({
                                "issue": "Confirmation Complete But No Trade",
                                "description": "Signal confirmed but trade not executing",
                                "severity": "critical"
                            })
                
                # Check recent trades
                last_trade = db.query(Trade).filter(Trade.bot_id == bot.id).order_by(Trade.executed_at.desc()).first()
                if last_trade and last_trade.status == "pending":
                    minutes_since = int((datetime.utcnow() - last_trade.executed_at).total_seconds() / 60) if last_trade.executed_at else 0
                    if minutes_since > 5:
                        bot_diagnosis["issues"].append({
                            "issue": "Pending Trade Stuck",
                            "description": f"Trade pending for {minutes_since} minutes",
                            "severity": "critical"
                        })
                
            except Exception as e:
                bot_diagnosis["issues"].append({
                    "issue": "Bot Evaluation Failed",
                    "description": str(e),
                    "severity": "critical"
                })
            
            diagnosis["bot_diagnoses"].append(bot_diagnosis)
        
        return diagnosis
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Diagnosis failed: {str(e)}")
