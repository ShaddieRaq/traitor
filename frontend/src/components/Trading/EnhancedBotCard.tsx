import React from 'react';
import { EnhancedBotStatus } from '../../types';
import { useBotPerformanceByPair } from '../../hooks/useBotPerformance';
import ConfirmationTimer from './ConfirmationTimer';
import SignalStrengthMeter from './SignalStrengthMeter';
import TradeReadinessBadge from './TradeReadinessBadge';
import TradeBlockingDiagnosis from './TradeBlockingDiagnosis';
import CooldownTimer from './CooldownTimer';

interface EnhancedBotCardProps {
  bot: EnhancedBotStatus;
  className?: string;
}

const EnhancedBotCard: React.FC<EnhancedBotCardProps> = ({ bot, className = '' }) => {
  // Get performance data for position value calculation
  const { data: performance } = useBotPerformanceByPair(bot.pair);
  
  // Calculate position value and formatting
  const positionValue = performance ? performance.current_position * performance.current_price : 0;
  const formatPositionValue = (value: number) => {
    if (value < 0.01) return '$0.00';
    if (value < 1000) return `$${value.toFixed(2)}`;
    if (value < 1000000) return `$${(value / 1000).toFixed(1)}k`;
    return `$${(value / 1000000).toFixed(1)}M`;
  };
  
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

  const tempConfig = getTemperatureConfig(bot.temperature);

  return (
    <div className={`bg-white rounded-lg border-2 ${tempConfig.bg} p-4 ${className}`}>
      {/* Header */}
      <div className="flex items-center justify-between mb-3">
        <div className="flex items-center space-x-3">
          <div className="flex items-center space-x-2">
            <h3 className="text-lg font-semibold text-gray-900">{bot.name}</h3>
            <span className="text-2xl">{tempConfig.emoji}</span>
          </div>
          <div className="text-sm text-gray-500">{bot.pair}</div>
        </div>
        <div className="flex items-center space-x-2">
          <span className={`px-2 py-1 rounded text-xs font-medium ${
            bot.status === 'RUNNING' 
              ? 'bg-green-100 text-green-800' 
              : 'bg-gray-100 text-gray-600'
          }`}>
            {bot.status}
          </span>
        </div>
      </div>

      {/* Signal Score and Temperature */}
      <div className="flex items-center justify-between mb-3">
        <div className="flex items-center space-x-4">
          <div className="text-sm">
            <span className="text-gray-500">Score:</span>
            <span className={`ml-1 font-mono font-medium ${
              bot.current_combined_score > 0 ? 'text-red-600' : 
              bot.current_combined_score < 0 ? 'text-green-600' : 'text-gray-600'
            }`}>
              {bot.current_combined_score.toFixed(3)}
            </span>
          </div>
          <div className={`text-sm font-medium ${tempConfig.color}`}>
            {bot.temperature}
          </div>
        </div>
        <div className="text-sm text-gray-500">
          {bot.pair} • {formatPositionValue(positionValue)}
        </div>
      </div>

      {/* Signal Strength Meter */}
      <div className="mb-3">
        <SignalStrengthMeter intent={bot.trading_intent} />
      </div>

      {/* Confirmation Timer */}
      {bot.confirmation.is_active && (
        <div className="mb-3">
          <ConfirmationTimer confirmation={bot.confirmation} />
        </div>
      )}

      {/* Cooldown Timer - Always visible when active */}
      {bot.trade_readiness.cooldown_remaining_minutes > 0 && (
        <div className="mb-3">
          <CooldownTimer cooldownMinutes={bot.trade_readiness.cooldown_remaining_minutes} />
        </div>
      )}

      {/* Trade Readiness */}
      <div className="mb-3">
        <TradeReadinessBadge readiness={bot.trade_readiness} />
      </div>

      {/* Trade Blocking Diagnosis */}
      <div className="border-t pt-3">
        <TradeBlockingDiagnosis bot={bot} className="mb-3" />
      </div>

      {/* Quick Stats */}
      <div className="border-t pt-3 mt-3">
        <div className="grid grid-cols-2 gap-4 text-xs">
          <div>
            <span className="text-gray-500">Distance to Signal:</span>
            <div className="font-mono text-gray-700">
              {bot.distance_to_signal.toFixed(3)}
            </div>
          </div>
          <div>
            <span className="text-gray-500">Next Action:</span>
            <div className={`font-medium ${
              bot.trading_intent.next_action === 'buy' ? 'text-green-600' :
              bot.trading_intent.next_action === 'sell' ? 'text-red-600' : 'text-gray-600'
            }`}>
              {bot.trading_intent.next_action.toUpperCase()}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default EnhancedBotCard;
