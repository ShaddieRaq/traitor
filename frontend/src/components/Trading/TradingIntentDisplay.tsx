import React from 'react';
import { EnhancedBotStatus } from '../../types';

interface TradingIntentDisplayProps {
  bot: EnhancedBotStatus;
}

const TradingIntentDisplay: React.FC<TradingIntentDisplayProps> = ({ bot }) => {
  const getTradingIntent = () => {
    const intent = bot.trading_intent;
    const confirmation = bot.confirmation;
    const readiness = bot.trade_readiness;

    if (!intent) {
      return {
        action: 'HOLD',
        strength: 'None',
        color: 'text-gray-600',
        bgColor: 'bg-gray-50',
        icon: '⏸️',
        status: 'No signal'
      };
    }

    const action = intent.next_action?.toUpperCase() || 'HOLD';
    const strength = intent.signal_strength || 0;
    
    // Determine color based on action and strength
    let color = 'text-gray-600';
    let bgColor = 'bg-gray-50';
    let icon = '⏸️';
    
    if (action === 'BUY') {
      color = strength > 0.7 ? 'text-green-700' : strength > 0.4 ? 'text-green-600' : 'text-green-500';
      bgColor = strength > 0.7 ? 'bg-green-100' : strength > 0.4 ? 'bg-green-50' : 'bg-green-25';
      icon = '📈';
    } else if (action === 'SELL') {
      color = strength > 0.7 ? 'text-red-700' : strength > 0.4 ? 'text-red-600' : 'text-red-500';
      bgColor = strength > 0.7 ? 'bg-red-100' : strength > 0.4 ? 'bg-red-50' : 'bg-red-25';
      icon = '📉';
    }

    // Get status based on confirmation and readiness
    let status = 'Monitoring';
    if (confirmation?.is_active && readiness?.can_trade) {
      status = 'Ready to Execute';
    } else if (confirmation?.is_active) {
      status = `Confirming (${confirmation.time_remaining_seconds}s)`;
    } else if (!readiness?.can_trade && readiness?.blocking_reason) {
      status = 'Blocked';
    }

    return {
      action,
      strength: strength > 0.8 ? 'Very Strong' : 
                strength > 0.6 ? 'Strong' : 
                strength > 0.4 ? 'Moderate' : 
                strength > 0.2 ? 'Weak' : 'Very Weak',
      strengthValue: strength,
      color,
      bgColor,
      icon,
      status
    };
  };

  const intent = getTradingIntent();

  return (
    <div className={`p-4 rounded-lg border ${intent.bgColor}`}>
      <div className="flex items-center justify-between">
        <div className="flex items-center space-x-3">
          <div className="text-2xl">{intent.icon}</div>
          <div>
            <div className={`text-lg font-bold ${intent.color}`}>
              {intent.action}
            </div>
            <div className="text-sm text-gray-600">
              {intent.strength} Signal
            </div>
          </div>
        </div>
        
        <div className="text-right">
          <div className="text-sm font-medium text-gray-900">
            {intent.status}
          </div>
          {intent.strengthValue && intent.strengthValue > 0 && (
            <div className="text-xs text-gray-500">
              {(intent.strengthValue * 100).toFixed(0)}% confidence
            </div>
          )}
        </div>
      </div>
      
      {/* Signal strength bar */}
      {intent.strengthValue && intent.strengthValue > 0 && (
        <div className="mt-3">
          <div className="flex justify-between text-xs text-gray-500 mb-1">
            <span>Signal Strength</span>
            <span>{(intent.strengthValue * 100).toFixed(0)}%</span>
          </div>
          <div className="w-full bg-gray-200 rounded-full h-2">
            <div 
              className={`h-2 rounded-full transition-all duration-300 ${
                intent.action === 'BUY' ? 'bg-green-500' : 'bg-red-500'
              }`}
              style={{ width: `${intent.strengthValue * 100}%` }}
            ></div>
          </div>
        </div>
      )}
      
      {/* Confirmation timer */}
      {bot.confirmation?.is_active && bot.confirmation.time_remaining_seconds > 0 && (
        <div className="mt-3 p-2 bg-yellow-50 border border-yellow-200 rounded">
          <div className="flex items-center justify-between">
            <div className="text-sm text-yellow-800">
              <span className="animate-pulse">⏳</span> Confirming signal...
            </div>
            <div className="text-sm font-medium text-yellow-700">
              {bot.confirmation.time_remaining_seconds}s remaining
            </div>
          </div>
        </div>
      )}
      
      {/* Ready to execute */}
      {bot.confirmation?.is_active && bot.trade_readiness?.can_trade && (
        <div className="mt-3 p-2 bg-green-50 border border-green-200 rounded">
          <div className="flex items-center justify-between">
            <div className="text-sm text-green-800">
              🚀 Ready to execute {intent.action.toLowerCase()}
            </div>
            <div className="text-sm font-medium text-green-700">
              Execute Now
            </div>
          </div>
        </div>
      )}
      
      {/* Blocking reason */}
      {!bot.trade_readiness?.can_trade && bot.trade_readiness?.blocking_reason && (
        <div className="mt-3 p-2 bg-red-50 border border-red-200 rounded">
          <div className="text-sm text-red-800">
            ⛔ {bot.trade_readiness.blocking_reason}
          </div>
        </div>
      )}
    </div>
  );
};

export default TradingIntentDisplay;
