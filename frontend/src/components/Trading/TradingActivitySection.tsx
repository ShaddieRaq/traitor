import React from 'react';
import { EnhancedBotStatus } from '../../types';

interface SimpleActivityItemProps {
  bot: EnhancedBotStatus;
}

const SimpleActivityItem: React.FC<SimpleActivityItemProps> = ({ bot }) => {
  const botData = bot as any;
  
  // Determine the most important current activity for this bot
  const getCurrentActivity = () => {
    // 1. If confirming and can trade - show ready to execute
    if (botData.confirmation?.is_active && botData.trade_readiness?.can_trade) {
      return {
        type: 'ready_to_trade',
        message: `Ready to ${botData.trading_intent?.next_action?.toUpperCase() || 'TRADE'}`,
        icon: '🚀',
        color: 'bg-green-500',
        status: 'Ready to Execute',
        time: 'Now'
      };
    }
    
    // 2. If confirming with timer - show confirming
    if (botData.confirmation?.is_active && botData.confirmation.time_remaining_seconds > 0) {
      return {
        type: 'confirming',
        message: `Confirming ${botData.trading_intent?.next_action?.toUpperCase()} signal`,
        icon: '⏳',
        color: 'bg-yellow-500 animate-pulse',
        status: 'Confirming',
        time: `${botData.confirmation.time_remaining_seconds}s left`
      };
    }
    
    // 3. Recent trade activity
    if (botData.last_trade?.minutes_ago <= 30) {
      const side = botData.last_trade.side?.toUpperCase();
      const amount = botData.last_trade.size?.toFixed(2) || botData.last_trade.price?.toFixed(2);
      return {
        type: 'recent_trade',
        message: `${side} $${amount}`,
        icon: side === 'BUY' ? '📈' : '📉',
        color: side === 'BUY' ? 'bg-green-500' : 'bg-red-500',
        status: side === 'BUY' ? 'Purchased' : 'Sold',
        time: `${botData.last_trade.minutes_ago}m ago`
      };
    }
    
    // 4. Default monitoring state
    return {
      type: 'monitoring',
      message: 'Monitoring market conditions',
      icon: '👁️',
      color: 'bg-gray-400',
      status: 'Monitoring',
      time: 'Live'
    };
  };

  const activity = getCurrentActivity();

  return (
    <div className="flex items-center justify-between py-3 border-b border-gray-100 last:border-b-0">
      <div className="flex items-center">
        <div className={`w-3 h-3 rounded-full mr-3 ${activity.color}`}></div>
        <div>
          <div className="text-sm text-gray-900">
            <span className="font-medium">{bot.name}</span> {activity.message}
          </div>
          <div className="text-xs text-gray-500 mt-0.5">
            {activity.icon} {activity.status}
          </div>
        </div>
      </div>
      <div className="text-right">
        <div className="text-xs text-gray-500">{activity.time}</div>
      </div>
    </div>
  );
};

interface TradingActivitySectionProps {
  bots: EnhancedBotStatus[];
}

const TradingActivitySection: React.FC<TradingActivitySectionProps> = ({ bots }) => {
  if (!bots || bots.length === 0) {
    return (
      <div className="bg-white shadow rounded-lg">
        <div className="px-4 py-5 sm:p-6">
          <h3 className="text-lg leading-6 font-medium text-gray-900 mb-4">
            Trading Activity
          </h3>
          <div className="text-center py-8">
            <div className="text-gray-400 text-2xl mb-2">📊</div>
            <div className="text-sm text-gray-500">No trading activity</div>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="bg-white shadow rounded-lg">
      <div className="px-4 py-5 sm:p-6">
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-lg leading-6 font-medium text-gray-900">
            Trading Activity
          </h3>
          <div className="flex items-center">
            <div className="w-2 h-2 bg-green-400 rounded-full animate-pulse mr-1"></div>
            <span className="text-xs text-gray-500">Live</span>
          </div>
        </div>
        
        <div className="space-y-1">
          {bots.map((bot) => (
            <SimpleActivityItem key={bot.id} bot={bot} />
          ))}
        </div>
      </div>
    </div>
  );
};

export default TradingActivitySection;
