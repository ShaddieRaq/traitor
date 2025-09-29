import React from 'react';
import { useEnhancedBotsStatus, usePnLData } from '../../hooks/useBots';

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
  const { data: pnlData } = usePnLData();
  const botsData = propBotsData || hookBotsData;

  if (!botsData) {
    return <div className={`animate-pulse bg-gray-100 rounded-lg h-64 ${className}`}></div>;
  }

  // Group bots by temperature
  const groupedBots = {
    HOT: botsData.filter(bot => bot.temperature === 'HOT'),
    WARM: botsData.filter(bot => bot.temperature === 'WARM'),
    COOL: botsData.filter(bot => bot.temperature === 'COOL'),
    FROZEN: botsData.filter(bot => bot.temperature === 'FROZEN')
  };

  const TemperatureGroup = ({ title, icon, bots, bgColor }: { title: string; icon: string; bots: any[]; bgColor: string }) => {
    if (bots.length === 0) return null;
    
    return (
      <div className="border rounded-lg border-gray-200 bg-gray-50 mb-4">
        <div className={`px-4 py-3 border-b border-gray-200 ${bgColor}`}>
          <div className="font-medium text-gray-900 flex items-center space-x-2">
            <span className="text-xl">{icon}</span>
            <span>{title} ({bots.length})</span>
          </div>
        </div>
        <div className="p-4 space-y-3">
          {bots.map((bot: any) => (
            <BotCard key={bot.id} bot={bot} pnlData={pnlData} />
          ))}
        </div>
      </div>
    );
  };

  return (
    <div className={`space-y-4 ${className}`}>
      <TemperatureGroup 
        title="HOT BOTS" 
        icon="🔥" 
        bots={groupedBots.HOT} 
        bgColor="bg-gradient-to-r from-red-50 to-orange-50" 
      />
      <TemperatureGroup 
        title="WARM BOTS" 
        icon="🌡️" 
        bots={groupedBots.WARM} 
        bgColor="bg-gradient-to-r from-orange-50 to-yellow-50" 
      />
      <TemperatureGroup 
        title="COOL BOTS" 
        icon="❄️" 
        bots={groupedBots.COOL} 
        bgColor="bg-gradient-to-r from-blue-50 to-cyan-50" 
      />
      <TemperatureGroup 
        title="FROZEN BOTS" 
        icon="🧊" 
        bots={groupedBots.FROZEN} 
        bgColor="bg-gradient-to-r from-gray-50 to-slate-50" 
      />
    </div>
  );
};

interface BotCardProps {
  bot: any;
  pnlData?: any[];
}

const BotCard: React.FC<BotCardProps> = ({ bot, pnlData }) => {
  // Find P&L data for this bot's pair
  const botPnL = pnlData?.find(p => p.product_id === bot.pair);
  
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
    const score = bot.current_combined_score || 0;
    const confidence = bot.trading_intent?.confidence || 0;
    if (score < -0.05) {
      return { text: 'BUY SIGNAL', action: 'BUY', color: 'text-green-700 bg-green-100 border-green-300', emoji: '🟢', confidence };
    } else if (score > 0.05) {
      return { text: 'SELL SIGNAL', action: 'SELL', color: 'text-red-700 bg-red-100 border-red-300', emoji: '🔴', confidence };
    }
    return { text: 'HOLD', action: 'HOLD', color: 'text-yellow-700 bg-yellow-100 border-yellow-300', emoji: '🟡', confidence };
  };

  const formatPnL = (pnl: number) => {
    const sign = pnl >= 0 ? '+' : '';
    const color = pnl >= 0 ? 'text-green-600' : 'text-red-600';
    return {
      value: `${sign}$${Math.abs(pnl).toFixed(2)}`,
      color
    };
  };

  const formatPnLPercent = (pnl: number, totalSpent: number) => {
    if (totalSpent === 0) return { value: '0.0%', color: 'text-gray-500' };
    const percent = (pnl / totalSpent) * 100;
    const sign = percent >= 0 ? '+' : '';
    const color = percent >= 0 ? 'text-green-600' : 'text-red-600';
    return {
      value: `${sign}${percent.toFixed(1)}%`,
      color
    };
  };

  const signal = getSignalDisplay();
  const pnlFormatted = botPnL ? formatPnL(botPnL.net_pnl_usd) : { value: 'N/A', color: 'text-gray-500' };
  const pnlPercentFormatted = botPnL ? formatPnLPercent(botPnL.net_pnl_usd, botPnL.total_spent_usd) : { value: 'N/A', color: 'text-gray-500' };

  return (
    <div className="bg-white rounded-lg p-4 border hover:shadow-md transition-shadow">
      {/* Header: Pair + P&L */}
      <div className="flex items-center justify-between mb-3">
        <div className="flex items-center space-x-2">
          <span className="text-lg">{getTemperatureIcon()}</span>
          <div className="font-bold text-lg text-gray-900">{bot.pair}</div>
        </div>
        <div className="text-right">
          <div className={`font-bold text-sm ${pnlFormatted.color}`}>
            {pnlFormatted.value}
          </div>
          <div className={`text-xs ${pnlPercentFormatted.color}`}>
            {pnlPercentFormatted.value}
          </div>
        </div>
      </div>

      {/* Signal + Confidence */}
      <div className="mb-3">
        <div className={`text-sm font-medium px-3 py-2 rounded-lg border ${signal.color}`}>
          {signal.emoji} {signal.text} ({Math.round(signal.confidence * 100)}%)
        </div>
      </div>

      {/* Key Metrics Grid */}
      <div className="grid grid-cols-2 gap-3 text-sm mb-3">
        <div className="bg-gray-50 rounded-lg p-2">
          <div className="text-gray-600 font-medium text-xs">Position Risk</div>
          <div className="font-bold">
            {bot.current_position_size ? 
              `$${Math.abs(bot.current_position_size).toFixed(0)}/${bot.position_size_usd || '20'}` :
              '$0/$20'
            }
          </div>
          <div className="text-xs text-gray-500">
            {bot.current_position_size ? 
              `${Math.round((Math.abs(bot.current_position_size) / (bot.position_size_usd || 20)) * 100)}%` :
              '0%'
            }
          </div>
        </div>
        <div className="bg-gray-50 rounded-lg p-2">
          <div className="text-gray-600 font-medium text-xs">Activity</div>
          <div className="font-bold">
            {bot.last_trade?.minutes_ago 
              ? `${bot.last_trade.minutes_ago < 60 
                  ? `${bot.last_trade.minutes_ago}m ago`
                  : bot.last_trade.minutes_ago < 1440
                    ? `${Math.floor(bot.last_trade.minutes_ago / 60)}h ago`
                    : `${Math.floor(bot.last_trade.minutes_ago / 1440)}d ago`
                }`
              : 'None'
            }
          </div>
          <div className="text-xs text-gray-500">
            {botPnL ? `${botPnL.trade_count} trades` : '0 trades'}
          </div>
        </div>
      </div>

      {/* Status */}
      {bot.trade_readiness && (
        <div className={`text-xs px-2 py-1 rounded text-center ${
          bot.trade_readiness.can_trade 
            ? 'text-green-700 bg-green-50' 
            : 'text-yellow-700 bg-yellow-50'
        }`}>
          {bot.trade_readiness.can_trade ? '✅ Ready to trade' : '⏸️ Monitoring'}
        </div>
      )}
    </div>
  );
};

export default TieredBotsView;
