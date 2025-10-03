import React from 'react';
import { EnhancedBotStatus } from '../../types';
import BotPerformanceSection from './BotPerformanceSection';
import SignalStrengthMeter from './SignalStrengthMeter';
import SignalConfidenceMeter from './SignalConfidenceMeter';
import CircularConfirmationTimer from './CircularConfirmationTimer';
import ErrorIndicator from './ErrorIndicator';
import { useBotPerformanceByPair } from '../../hooks/useBotPerformance';

interface ConsolidatedBotCardProps {
  bot: EnhancedBotStatus;
  className?: string;
}

const ConsolidatedBotCard: React.FC<ConsolidatedBotCardProps> = ({ bot, className = '' }) => {
  // Get performance data for position value calculation
  const { data: performance } = useBotPerformanceByPair(bot.pair);
  
  // Get primary display data
  const tradingIntent = bot.trading_intent;
  const confirmation = bot.confirmation;
  const readiness = bot.trade_readiness;
  
  // Determine primary action and strength
  const action = tradingIntent?.next_action?.toUpperCase() || 'HOLD';
  const signalStrength = tradingIntent?.signal_strength || 0;
  
  // Calculate position value (coins * current price)
  const positionValue = performance ? performance.current_position * performance.current_price : 0;
  const formatPositionValue = (value: number) => {
    if (value < 0.01) return '$0.00';
    if (value < 1000) return `$${value.toFixed(2)}`;
    if (value < 1000000) return `$${(value / 1000).toFixed(1)}k`;
    return `$${(value / 1000000).toFixed(1)}M`;
  };
  
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
    // PRIORITY 0: Optimization status (highest priority)
    if (bot.optimization_status?.skipped) {
      return { 
        text: 'Signals Skipped', 
        color: 'text-purple-700', 
        bgColor: 'bg-purple-100',
        icon: '⚡'
      };
    }
    
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
            <ErrorIndicator botId={bot.id} botName={bot.name} />
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
            {bot.pair} • {formatPositionValue(positionValue)}
          </div>
        </div>
      </div>

      {/* SIGNAL ANALYSIS: Three Circles - Strength, Confidence, Confirmation */}
      {signalStrength > 0 && (
        <div className="mb-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-4">
              <SignalStrengthMeter 
                intent={bot.trading_intent}
              />
              <SignalConfidenceMeter 
                intent={bot.trading_intent}
              />
              <CircularConfirmationTimer 
                confirmation={bot.confirmation} 
                tradingIntent={bot.trading_intent}
              />
            </div>
          </div>
        </div>
      )}

      {/* BOT PERFORMANCE: Position-based P&L tracking */}
      <BotPerformanceSection 
        productId={bot.pair}
        compact={false}
      />

      {/* BLOCKING REASON: Only show if there's a blocking reason */}
      {readiness?.blocking_reason && (
        <div className="mt-3 p-2 bg-red-50 border border-red-200 rounded text-xs">
          <span className="text-red-700 font-medium">⚠️ Trading Blocked:</span>
          <div className="text-red-600 mt-1">
            {readiness.blocking_reason}
          </div>
        </div>
      )}

      {/* OPTIMIZATION STATUS: Show when signals are skipped for performance */}
      {bot.optimization_status?.skipped && (
        <div className="mt-3 p-2 bg-purple-50 border border-purple-200 rounded text-xs">
          <span className="text-purple-700 font-medium">⚡ Performance Optimization:</span>
          <div className="text-purple-600 mt-1">
            {bot.optimization_status.reason}
          </div>
        </div>
      )}
    </div>
  );
};

export default React.memo(ConsolidatedBotCard);
