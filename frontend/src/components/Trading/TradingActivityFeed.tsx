import React from 'react';
import { EnhancedBotStatus } from '../../types';
import { useTrades } from '../../hooks/useTrades';

interface TradingActivityFeedProps {
  bots: EnhancedBotStatus[];
  className?: string;
}

const TradingActivityFeed: React.FC<TradingActivityFeedProps> = ({ bots, className = '' }) => {
  // Fetch actual trade data
  const { data: trades, isLoading: tradesLoading } = useTrades(10);

  // Generate activity items from bot data and actual trades
  const generateActivityItems = () => {
    const activities: Array<{
      id: string;
      type: 'confirmation' | 'ready' | 'trade' | 'signal';
      botName: string;
      message: string;
      timestamp: Date;
      status: 'active' | 'ready' | 'completed';
      color: string;
      action?: string;
    }> = [];

    bots.forEach(bot => {
      const botData = bot as any;

      // Active confirmation timers
      if (botData.confirmation?.is_active) {
        const endTime = new Date(botData.confirmation.end_time);
        const remainingSeconds = Math.max(0, Math.ceil((endTime.getTime() - Date.now()) / 1000));
        
        activities.push({
          id: `confirmation-${bot.id}`,
          type: 'confirmation',
          botName: bot.name,
          message: `Confirming ${botData.trading_intent?.next_action?.toUpperCase()} signal (${remainingSeconds}s left)`,
          timestamp: new Date(botData.confirmation.start_time),
          status: 'active',
          color: botData.trading_intent?.next_action === 'buy' ? 'bg-green-500' : 'bg-red-500',
          action: botData.trading_intent?.next_action
        });
      }

      // Trade readiness
      if (botData.trade_readiness?.is_ready) {
        activities.push({
          id: `ready-${bot.id}`,
          type: 'ready',
          botName: bot.name,
          message: `Ready to ${botData.trading_intent?.next_action?.toUpperCase()}`,
          timestamp: new Date(),
          status: 'ready',
          color: 'bg-orange-500',
          action: botData.trading_intent?.next_action
        });
      }

      // Signal strength alerts (for strong signals)
      if (botData.trading_intent?.signal_strength >= 0.8) {
        activities.push({
          id: `signal-${bot.id}`,
          type: 'signal',
          botName: bot.name,
          message: `Strong ${botData.trading_intent.next_action?.toUpperCase()} signal (${(botData.trading_intent.signal_strength * 100).toFixed(0)}%)`,
          timestamp: new Date(),
          status: 'active',
          color: 'bg-blue-500',
          action: botData.trading_intent.next_action
        });
      }
    });

    // Add actual trade data from enhanced API
    if (trades && !tradesLoading) {
      trades.slice(0, 5).forEach((trade) => {
        const botName = bots.find(b => b.id === trade.bot_id)?.name || `Bot ${trade.bot_id}`;
        activities.push({
          id: `actual-trade-${trade.id}`,
          type: 'trade',
          botName,
          message: `${trade.action || trade.side?.toUpperCase()} $${trade.amount?.toFixed(2) || (trade.size * trade.price).toFixed(2)}`,
          timestamp: new Date(trade.created_at),
          status: trade.status === 'filled' ? 'completed' : trade.status === 'pending' ? 'active' : 'completed',
          color: (trade.action === 'BUY' || trade.side === 'buy') ? 'bg-green-500' : 'bg-red-500',
          action: trade.action?.toLowerCase() || trade.side
        });
      });
    }

    // Sort by timestamp, most recent first
    return activities.sort((a: any, b: any) => b.timestamp.getTime() - a.timestamp.getTime()).slice(0, 10);
  };

  const activities = generateActivityItems();

  if (activities.length === 0) {
    return (
      <div className={`bg-white rounded-lg border border-gray-200 p-6 ${className}`}>
        <h3 className="text-lg font-medium text-gray-900 mb-4">Trading Activity</h3>
        <div className="text-center py-8">
          <div className="text-gray-400 text-4xl mb-2">📈</div>
          <div className="text-sm text-gray-500">No recent trading activity</div>
        </div>
      </div>
    );
  }

  return (
    <div className={`bg-white rounded-lg border border-gray-200 p-6 ${className}`}>
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-lg font-medium text-gray-900">Trading Activity</h3>
        <div className="flex items-center space-x-1">
          <div className="w-2 h-2 bg-green-400 rounded-full animate-pulse"></div>
          <span className="text-xs text-gray-500">Live</span>
        </div>
      </div>
      
      <div className="space-y-3 max-h-96 overflow-y-auto">
        {activities.map((activity) => (
          <div key={activity.id} className="flex items-start space-x-3 p-3 rounded-lg hover:bg-gray-50 transition-colors">
            <div className={`w-3 h-3 rounded-full mt-1 ${activity.color} ${
              activity.status === 'active' ? 'animate-pulse' : ''
            }`}></div>
            
            <div className="flex-1 min-w-0">
              <div className="flex items-center justify-between">
                <div className="flex items-center space-x-2">
                  <span className="text-sm font-medium text-gray-900">{activity.botName}</span>
                  <span className={`text-xs px-2 py-1 rounded ${
                    activity.status === 'active' ? 'bg-orange-100 text-orange-700' :
                    activity.status === 'ready' ? 'bg-yellow-100 text-yellow-700' :
                    'bg-gray-100 text-gray-600'
                  }`}>
                    {activity.status === 'active' ? 'Active' :
                     activity.status === 'ready' ? 'Ready' : 'Completed'}
                  </span>
                </div>
                <span className="text-xs text-gray-500">
                  {activity.timestamp.toLocaleTimeString()}
                </span>
              </div>
              
              <p className="text-sm text-gray-600 mt-1">{activity.message}</p>
              
              {activity.type === 'confirmation' && (
                <div className="mt-2">
                  <div className="flex items-center space-x-2">
                    <div className="flex-1 bg-gray-200 rounded-full h-1">
                      <div 
                        className={`h-1 rounded-full transition-all duration-1000 ${
                          activity.action === 'buy' ? 'bg-green-500' : 'bg-red-500'
                        }`}
                        style={{ 
                          width: `${Math.max(10, 100 - (parseInt(activity.message.match(/\((\d+)s/)?.[1] || '0') / 30) * 100)}%` 
                        }}
                      ></div>
                    </div>
                    <span className="text-xs text-gray-500">
                      {activity.message.match(/\((\d+)s/)?.[1] || '0'}s
                    </span>
                  </div>
                </div>
              )}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};

export default TradingActivityFeed;
