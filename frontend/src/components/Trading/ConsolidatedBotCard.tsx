import React from 'react';
import { EnhancedBotStatus } from '../../types';

interface ConsolidatedBotCardProps {
  bot: EnhancedBotStatus;
  className?: string;
}

const ConsolidatedBotCard: React.FC<ConsolidatedBotCardProps> = ({ bot, className = '' }) => {
  // Get primary display data
  const tradingIntent = bot.trading_intent;
  const confirmation = bot.confirmation;
  const readiness = bot.trade_readiness;
  
  // Determine primary action and strength
  const action = tradingIntent?.next_action?.toUpperCase() || 'HOLD';
  const signalStrength = tradingIntent?.signal_strength || 0;
  const confidence = tradingIntent?.confidence || 0;
  
  // Get temperature config
  const getTemperatureConfig = (temperature: string) => {
    switch (temperature) {
      case 'HOT':
        return { emoji: '🔥', color: 'text-red-600', bg: 'bg-red-50 border-red-200' };
      case 'WARM':
        return { emoji: '🌡️', color: 'text-orange-600', bg: 'bg-orange-50 border-orange-200' };
      case 'COOL':
        return { emoji: '❄️', color: 'text-blue-600', bg: 'bg-blue-50 border-blue-200' };
      case 'FROZEN':
        return { emoji: '🧊', color: 'text-gray-600', bg: 'bg-gray-50 border-gray-200' };
      default:
        return { emoji: '❓', color: 'text-gray-600', bg: 'bg-gray-50 border-gray-200' };
    }
  };

  // Get action config
  const getActionConfig = (action: string, strength: number) => {
    if (action === 'BUY') {
      return {
        icon: '📈',
        color: strength > 0.6 ? 'text-green-700' : 'text-green-600',
        bgColor: strength > 0.6 ? 'bg-green-100' : 'bg-green-50',
        barColor: 'bg-green-500'
      };
    } else if (action === 'SELL') {
      return {
        icon: '📉',
        color: strength > 0.6 ? 'text-red-700' : 'text-red-600',
        bgColor: strength > 0.6 ? 'bg-red-100' : 'bg-red-50',
        barColor: 'bg-red-500'
      };
    }
    return {
      icon: '⏸️',
      color: 'text-gray-600',
      bgColor: 'bg-gray-50',
      barColor: 'bg-gray-400'
    };
  };

  // Get status info
  const getStatusInfo = () => {
    // PRIORITY 1: Cooldown status (overrides everything else)
    if (readiness?.cooldown_remaining_minutes > 0 || readiness?.blocking_reason === 'cooldown') {
      const minutes = readiness?.cooldown_remaining_minutes || 0;
      return { 
        text: `Cooldown (${minutes}m)`, 
        color: 'text-blue-700', 
        bgColor: 'bg-blue-100',
        icon: '⏲️'
      };
    }
    
    // PRIORITY 2: Other blocking reasons
    if (!readiness?.can_trade && readiness?.blocking_reason && readiness?.blocking_reason !== 'cooldown') {
      return { text: 'Blocked', color: 'text-red-700', bgColor: 'bg-red-100', icon: '⛔' };
    }
    
    // PRIORITY 3: Confirmation states (only if not blocked)
    if (confirmation?.is_active && readiness?.can_trade) {
      return { text: 'Ready to Execute', color: 'text-green-700', bgColor: 'bg-green-100', icon: '✅' };
    } else if (confirmation?.is_active && confirmation?.time_remaining_seconds > 0) {
      return { 
        text: `Confirming (${confirmation.time_remaining_seconds}s)`, 
        color: 'text-yellow-700', 
        bgColor: 'bg-yellow-100',
        icon: '⏳'
      };
    }
    
    // PRIORITY 4: Low signal monitoring
    if (signalStrength < 0.3) {
      return { text: 'Monitoring', color: 'text-gray-600', bgColor: 'bg-gray-100', icon: '👁️' };
    }
    
    // DEFAULT: Active state
    return { text: 'Active', color: 'text-green-600', bgColor: 'bg-green-100', icon: '🟢' };
  };

  const tempConfig = getTemperatureConfig(bot.temperature);
  const actionConfig = getActionConfig(action, signalStrength);
  const statusInfo = getStatusInfo();

  return (
    <div className={`bg-white rounded-lg border-2 ${tempConfig.bg} p-4 shadow-sm ${className}`}>
      {/* PRIMARY SECTION: Essential Info */}
      <div className="flex items-center justify-between mb-4">
        {/* Left: Bot Identity + Primary Action */}
        <div className="flex items-center space-x-4">
          <div className="flex items-center space-x-2">
            <h3 className="text-lg font-semibold text-gray-900">{bot.name}</h3>
            <span className="text-2xl">{tempConfig.emoji}</span>
          </div>
          
          {/* Primary Action Indicator */}
          <div className={`flex items-center space-x-2 px-3 py-1.5 rounded-md ${actionConfig.bgColor}`}>
            <span className="text-lg">{actionConfig.icon}</span>
            <span className={`font-semibold ${actionConfig.color}`}>{action}</span>
            {signalStrength > 0 && (
              <span className="text-xs text-gray-600">
                {(signalStrength * 100).toFixed(0)}%
              </span>
            )}
          </div>
        </div>

        {/* Right: Status + Running State */}
        <div className="text-right">
          <div className={`inline-flex items-center px-2 py-1 rounded text-xs font-medium ${statusInfo.bgColor} ${statusInfo.color}`}>
            <span className="mr-1">{statusInfo.icon}</span>
            {statusInfo.text}
          </div>
          <div className="text-xs text-gray-500 mt-1">
            {bot.pair} • ${bot.current_position_size.toFixed(2)}
          </div>
        </div>
      </div>

      {/* SIGNAL STRENGTH: Single Consolidated Bar */}
      {signalStrength > 0 && (
        <div className="mb-4">
          <div className="flex justify-between text-sm text-gray-600 mb-2">
            <span>Signal Strength</span>
            <span>{(signalStrength * 100).toFixed(0)}% • {(confidence * 100).toFixed(0)}% confidence</span>
          </div>
          <div className="w-full bg-gray-200 rounded-full h-3">
            <div 
              className={`h-3 rounded-full transition-all duration-500 ${actionConfig.barColor}`}
              style={{ width: `${signalStrength * 100}%` }}
            ></div>
          </div>
        </div>
      )}

      {/* SECONDARY INFO: Expandable Technical Details */}
      <details className="group">
        <summary className="cursor-pointer text-xs text-gray-500 hover:text-gray-700 select-none">
          <span className="inline-flex items-center">
            Technical Details
            <svg className="w-3 h-3 ml-1 transition-transform group-open:rotate-90" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
            </svg>
          </span>
        </summary>
        
        <div className="mt-3 pt-3 border-t border-gray-200 grid grid-cols-2 gap-4 text-xs">
          <div>
            <span className="text-gray-500">Score:</span>
            <div className={`font-mono font-medium ${
              bot.current_combined_score > 0 ? 'text-red-600' : 
              bot.current_combined_score < 0 ? 'text-green-600' : 'text-gray-600'
            }`}>
              {bot.current_combined_score.toFixed(3)}
            </div>
          </div>
          <div>
            <span className="text-gray-500">Distance:</span>
            <div className="font-mono text-gray-700">
              {bot.distance_to_signal.toFixed(3)}
            </div>
          </div>
          {readiness?.blocking_reason && (
            <div className="col-span-2">
              <span className="text-gray-500">Blocking Reason:</span>
              <div className="text-red-600 text-xs mt-1">
                {readiness.blocking_reason}
              </div>
            </div>
          )}
        </div>
      </details>
    </div>
  );
};

export default ConsolidatedBotCard;
