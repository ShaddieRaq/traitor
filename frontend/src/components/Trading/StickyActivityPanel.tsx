import React, { useState } from 'react';
import { useTrades } from '../../hooks/useTrades';
import { EnhancedBotStatus } from '../../types';

interface ActivityItem {
  type: string;
  message: string;
  time: string;
  icon: string;
  color: string;
}

interface StickyActivityPanelProps {
  bots: EnhancedBotStatus[];
}

const StickyActivityPanel: React.FC<StickyActivityPanelProps> = ({ bots }) => {
  const [isExpanded, setIsExpanded] = useState(true);
  const { data: trades, isLoading } = useTrades(5); // Show last 5 trades
  
  const formatTime = (timestamp: string) => {
    const now = new Date();
    const tradeTime = new Date(timestamp);
    const diffMs = now.getTime() - tradeTime.getTime();
    const diffMins = Math.floor(diffMs / (1000 * 60));
    
    if (diffMins < 1) return 'now';
    if (diffMins < 60) return `${diffMins}m`;
    if (diffMins < 1440) return `${Math.floor(diffMins / 60)}h`;
    return `${Math.floor(diffMins / 1440)}d`;
  };

  const getActiveBotsCount = () => {
    return bots.filter(bot => 
      bot.confirmation?.is_active || 
      bot.trade_readiness?.can_trade ||
      bot.temperature === 'HOT'
    ).length;
  };

  const getRecentActivity = (): ActivityItem[] => {
    const activities: ActivityItem[] = [];
    
    // Add recent trade activities
    if (trades && trades.length > 0) {
      trades.slice(0, 2).forEach(trade => {
        activities.push({
          type: 'trade',
          message: `${trade.side} ${trade.product_id} at $${trade.price}`,
          time: formatTime(trade.created_at),
          icon: trade.side === 'BUY' ? '📈' : '📉',
          color: trade.side === 'BUY' ? 'text-green-600' : 'text-red-600'
        });
      });
    }
    
    // Add confirming bots
    bots.forEach(bot => {
      if (bot.confirmation?.is_active) {
        activities.push({
          type: 'confirming',
          message: `${bot.pair} confirming ${bot.trading_intent?.next_action?.toUpperCase()}`,
          time: bot.confirmation.time_remaining_seconds ? `${bot.confirmation.time_remaining_seconds}s` : 'now',
          icon: '⏳',
          color: 'text-yellow-600'
        });
      }
    });

    // Add ready bots with strong signals
    bots.forEach(bot => {
      if (bot.trade_readiness?.can_trade && !bot.confirmation?.is_active && 
          bot.current_combined_score && Math.abs(bot.current_combined_score) > 0.05) {
        activities.push({
          type: 'ready',
          message: `${bot.pair} ready to ${bot.trading_intent?.next_action?.toUpperCase()}`,
          time: 'now',
          icon: '🚀',
          color: 'text-orange-600'
        });
      }
    });

    return activities.slice(0, 3); // Show top 3 active items
  };

  const activeActivities = getRecentActivity();

  return (
    <div className="fixed right-4 top-20 z-40 w-80">
      <div className="bg-white border border-gray-200 rounded-lg shadow-lg">
        {/* Header */}
        <div className="flex items-center justify-between p-3 border-b border-gray-200 bg-gray-50 rounded-t-lg">
          <div className="flex items-center space-x-2">
            <div className="w-2 h-2 bg-green-400 rounded-full animate-pulse"></div>
            <h3 className="text-sm font-medium text-gray-900">Live Activity</h3>
            {getActiveBotsCount() > 0 && (
              <span className="bg-orange-100 text-orange-700 text-xs px-2 py-0.5 rounded-full">
                {getActiveBotsCount()} active
              </span>
            )}
          </div>
          <button
            onClick={() => setIsExpanded(!isExpanded)}
            className="text-gray-400 hover:text-gray-600 p-1"
          >
            {isExpanded ? '▼' : '▶'}
          </button>
        </div>

        {isExpanded && (
          <div className="max-h-96 overflow-y-auto">
            {/* Active Bot Activities */}
            {activeActivities.length > 0 && (
              <div className="p-3 border-b border-gray-100">
                <div className="text-xs font-medium text-gray-500 mb-2">ACTIVE NOW</div>
                <div className="space-y-2">
                  {activeActivities.map((activity, index) => (
                    <div key={index} className="flex items-center justify-between text-sm">
                      <div className="flex items-center space-x-2 flex-1 min-w-0">
                        <span className="text-lg">{activity.icon}</span>
                        <span className={`${activity.color} truncate`}>
                          {activity.message}
                        </span>
                      </div>
                      <span className="text-xs text-gray-500 ml-2 flex-shrink-0">
                        {activity.time}
                      </span>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Recent Trades */}
            <div className="p-3">
              <div className="text-xs font-medium text-gray-500 mb-2">RECENT TRADES</div>
              {isLoading ? (
                <div className="flex items-center justify-center py-4">
                  <div className="w-4 h-4 border-2 border-gray-300 border-t-blue-400 rounded-full animate-spin"></div>
                </div>
              ) : trades && trades.length > 0 ? (
                <div className="space-y-2">
                  {trades.map((trade) => (
                    <div key={trade.id} className="flex items-center justify-between text-sm">
                      <div className="flex items-center space-x-2 flex-1 min-w-0">
                        <span className="text-lg">
                          {trade.side === 'BUY' ? '📈' : '📉'}
                        </span>
                        <div className="flex-1 min-w-0">
                          <div className="flex items-center space-x-1">
                            <span className={`font-medium ${trade.side === 'BUY' ? 'text-green-600' : 'text-red-600'}`}>
                              {trade.side}
                            </span>
                            <span className="text-gray-600">
                              ${trade.usd_value?.toFixed(0) || '0'}
                            </span>
                          </div>
                          <div className="text-xs text-gray-500 truncate">
                            {trade.product_id}
                          </div>
                        </div>
                      </div>
                      <div className="text-xs text-gray-500 text-right flex-shrink-0">
                        {formatTime(trade.created_at)}
                      </div>
                    </div>
                  ))}
                </div>
              ) : (
                <div className="text-center py-4">
                  <div className="text-gray-400 text-lg mb-1">📊</div>
                  <div className="text-xs text-gray-500">No recent trades</div>
                </div>
              )}
            </div>

            {/* Quick Stats */}
            <div className="p-3 bg-gray-50 rounded-b-lg border-t border-gray-100">
              <div className="grid grid-cols-3 gap-2 text-center">
                <div>
                  <div className="text-lg font-semibold text-gray-900">{bots.length}</div>
                  <div className="text-xs text-gray-500">Bots</div>
                </div>
                <div>
                  <div className="text-lg font-semibold text-orange-600">{getActiveBotsCount()}</div>
                  <div className="text-xs text-gray-500">Active</div>
                </div>
                <div>
                  <div className="text-lg font-semibold text-green-600">{trades?.length || 0}</div>
                  <div className="text-xs text-gray-500">Recent</div>
                </div>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default StickyActivityPanel;
