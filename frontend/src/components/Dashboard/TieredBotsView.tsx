import React from 'react';
import { useEnhancedBotsStatus } from '../../hooks/useBots';

interface TieredBotsViewProps {
  className?: string;
  botsData?: any[];
  showAllMode?: boolean;
}

export const TieredBotsView: React.FC<TieredBotsViewProps> = ({ 
  className = '',
  botsData: propBotsData
}) => {
  const { data: hookBotsData } = useEnhancedBotsStatus();
  const botsData = propBotsData || hookBotsData;

  if (!botsData) {
    return <div className={`animate-pulse bg-gray-100 rounded-lg h-64 ${className}`}></div>;
  }

  return (
    <div className={`space-y-4 ${className}`}>
      <div className="border rounded-lg border-gray-200 bg-gray-50">
        <div className="px-4 py-3 border-b border-gray-200">
          <div className="font-medium text-gray-900">
            All Trading Bots ({botsData.length})
          </div>
          <div className="text-sm text-gray-600">Showing all {botsData.length} active trading bots</div>
        </div>
        <div className="p-4 space-y-3">
          {botsData.map((bot: any) => (
            <BotCard key={bot.id} bot={bot} />
          ))}
        </div>
      </div>
    </div>
  );
};

interface BotCardProps {
  bot: any;
}

const BotCard: React.FC<BotCardProps> = ({ bot }) => {
  const getTemperatureIcon = () => {
    switch (bot.temperature) {
      case 'HOT': return '🔥';
      case 'WARM': return '🌡️';
      case 'COOL': return '❄️';
      case 'FROZEN': return '🧊';
      default: return '⚪';
    }
  };

  const getSignalDisplay = () => {
    if (!bot.current_combined_score) return { text: 'HOLD', color: 'text-gray-700 bg-gray-100 border-gray-300', emoji: '🟡' };
    
    const score = bot.current_combined_score;
    if (score < -0.05) {
      return { text: 'BUY SIGNAL', color: 'text-green-700 bg-green-100 border-green-300', emoji: '🟢' };
    } else if (score > 0.05) {
      return { text: 'SELL SIGNAL', color: 'text-red-700 bg-red-100 border-red-300', emoji: '🔴' };
    }
    return { text: 'HOLD', color: 'text-yellow-700 bg-yellow-100 border-yellow-300', emoji: '🟡' };
  };

  const signal = getSignalDisplay();

  return (
    <div className="bg-white rounded-lg p-4 border hover:shadow-md transition-shadow">
      <div className="flex items-center justify-between mb-3">
        <div className="flex items-center space-x-3">
          <span className="text-xl">{getTemperatureIcon()}</span>
          <div>
            <div className="font-bold text-lg text-gray-900">{bot.symbol || bot.pair}</div>
            <div className="text-sm text-gray-600">{bot.name}</div>
          </div>
        </div>
        <div className="text-right">
          <span className="px-2 py-1 rounded-full text-xs font-medium bg-green-100 text-green-800">
            {bot.status}
          </span>
          <div className="text-xs text-gray-500 mt-1">{bot.temperature}</div>
        </div>
      </div>

      <div className="mb-3">
        <div className={`text-sm font-medium px-3 py-2 rounded-lg border ${signal.color}`}>
          {signal.emoji} {signal.text}
        </div>
        {bot.current_combined_score && typeof bot.current_combined_score === 'number' && (
          <div className="text-sm text-gray-700 mt-2 grid grid-cols-2 gap-3">
            <div>
              <span className="text-gray-600">Signal:</span>
              <span className="font-mono font-bold ml-1">{bot.current_combined_score.toFixed(3)}</span>
            </div>
            <div>
              <span className="text-gray-600">Strength:</span>
              <span className="font-bold ml-1">{(Math.abs(bot.current_combined_score) * 100).toFixed(1)}%</span>
            </div>
          </div>
        )}
      </div>

      <div className="grid grid-cols-2 gap-3 text-sm mb-3">
        <div className="bg-gray-50 rounded-lg p-3">
          <div className="text-gray-600 font-medium">Position Size</div>
          <div className="font-bold">${bot.current_position_size?.toFixed(2) || '0.00'}</div>
        </div>
        <div className="bg-gray-50 rounded-lg p-3">
          <div className="text-gray-600 font-medium">Last Trade</div>
          <div className="font-bold">{bot.last_trade_time || 'None'}</div>
        </div>
      </div>

      {bot.trade_readiness && (
        <div className="space-y-2">
          <div className={`text-sm px-3 py-2 rounded-lg ${
            bot.trade_readiness.can_trade 
              ? 'text-gray-700 bg-gray-50' 
              : 'text-yellow-700 bg-yellow-50'
          }`}>
            {bot.trade_readiness.can_trade ? '✅ Ready to trade' : '⏸️ Monitoring'}
          </div>
        </div>
      )}

      {bot.trading_intent && typeof bot.trading_intent === 'object' && (
        <div className="mt-3 text-sm">
          <div className="text-gray-600">Trading Intent:</div>
          <div className="font-medium text-gray-900">
            {bot.trading_intent.next_action || 'hold'} ({typeof bot.trading_intent.confidence === 'number' ? (bot.trading_intent.confidence * 100).toFixed(1) : '0'}% confidence)
          </div>
        </div>
      )}
    </div>
  );
};

export default TieredBotsView;
