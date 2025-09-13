import React from 'react';
import { useTrades, Trade } from '../../hooks/useTrades';
import { EnhancedBotStatus } from '../../types';

interface TradeActivityItemProps {
  trade: Trade;
  bot?: EnhancedBotStatus;
}

const TradeActivityItem: React.FC<TradeActivityItemProps> = ({ trade, bot }) => {
  const getTradeIcon = (side: string) => {
    if (side === 'BUY') return '📈';
    if (side === 'SELL') return '📉';
    return '💱';
  };

  // Clean data is always completed fills - no status needed
  const getStatusColor = () => {
    return 'bg-green-500'; // All raw trades are completed fills
  };

  const getStatusText = () => {
    return 'Completed'; // All raw trades are completed fills
  };

  const formatTime = (timestamp: string) => {
    const now = new Date();
    const tradeTime = new Date(timestamp);
    const diffMs = now.getTime() - tradeTime.getTime();
    const diffMins = Math.floor(diffMs / (1000 * 60));
    
    if (diffMins < 1) return 'Just now';
    if (diffMins < 60) return `${diffMins}m ago`;
    if (diffMins < 1440) return `${Math.floor(diffMins / 60)}h ago`;
    return `${Math.floor(diffMins / 1440)}d ago`;
  };

    const formatFullTimestamp = (dateString?: string) => {
    if (!dateString) return 'No timestamp';
    
    try {
      const date = new Date(dateString);
      return date.toLocaleString('en-US', {
        weekday: 'short',
        year: 'numeric',
        month: 'short',
        day: 'numeric',
        hour: 'numeric',
        minute: '2-digit',
        second: '2-digit',
        hour12: true
      });
    } catch {
      return 'Invalid date';
    }
  };

  const formatTimeOnly = (dateString?: string) => {
    if (!dateString) return '';
    
    try {
      const date = new Date(dateString);
      return date.toLocaleString('en-US', {
        hour: 'numeric',
        minute: '2-digit',
        hour12: true
      });
    } catch {
      return '';
    }
  };

    const formatAmount = (size: number, price: number, usd_value: number) => {
    // For clean data, we have usd_value directly
    if (usd_value && usd_value > 0) {
      return `$${usd_value.toFixed(2)}`;
    }
    
    // Fallback calculation if needed
    if (size && price) {
      return `$${(size * price).toFixed(2)}`;
    }
    
    return 'Amount pending';
  };

  return (
    <div className="flex items-center justify-between py-3 border-b border-gray-100 last:border-b-0">
      <div className="flex items-center">
        <div className={`w-3 h-3 rounded-full mr-3 ${getStatusColor()}`}></div>
        <div>
          <div className="text-sm text-gray-900">
            <span className="font-medium">{bot?.name || `${trade.product_id} Trade`}</span>
            {' '}
            <span className="text-gray-600">
              {trade.side} {formatAmount(trade.size, trade.price, trade.usd_value)}
            </span>
          </div>
          <div className="text-xs text-gray-500 mt-0.5">
            {getTradeIcon(trade.side)} {getStatusText()}
            {trade.order_id && (
              <span className="ml-2 text-gray-400">#{trade.order_id.slice(-8)}</span>
            )}
          </div>
        </div>
      </div>
      <div className="text-right">
        <div 
          className="text-xs text-gray-500 cursor-help" 
          title={formatFullTimestamp(trade.created_at)}
        >
          {formatTime(trade.created_at)}
        </div>
        <div className="text-xs text-gray-400 mt-0.5">
          {formatTimeOnly(trade.created_at)}
        </div>
      </div>
    </div>
  );
};

interface EnhancedTradingActivitySectionProps {
  bots: EnhancedBotStatus[];
}

const EnhancedTradingActivitySection: React.FC<EnhancedTradingActivitySectionProps> = ({ bots }) => {
  const { data: trades, isLoading, error, dataUpdatedAt } = useTrades(10);
  
  // Create a map of trading pair to bot data for clean trades lookup
  const botMap = new Map(bots.map(bot => [bot.pair, bot]));

  if (error) {
    return (
      <div className="bg-white shadow rounded-lg">
        <div className="px-4 py-5 sm:p-6">
          <h3 className="text-lg leading-6 font-medium text-gray-900 mb-4">
            Recent Trading Activity
          </h3>
          <div className="text-center py-8">
            <div className="text-red-400 text-2xl mb-2">⚠️</div>
            <div className="text-sm text-red-600">Failed to load trading activity</div>
            <div className="text-xs text-gray-500 mt-1">Check system status</div>
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
            Recent Trading Activity
          </h3>
          <div className="flex items-center space-x-2">
            {isLoading && (
              <div className="flex items-center space-x-1">
                <div className="w-2 h-2 bg-blue-400 rounded-full animate-spin"></div>
                <span className="text-xs text-gray-500">Loading...</span>
              </div>
            )}
            <span className="text-xs text-gray-400">
              Updated {formatTime(new Date(dataUpdatedAt).toISOString())}
            </span>
          </div>
        </div>
        
        {!trades || trades.length === 0 ? (
          <div className="text-center py-8">
            <div className="text-gray-400 text-2xl mb-2">📊</div>
            <div className="text-sm text-gray-500">No recent trading activity</div>
            <div className="text-xs text-gray-400 mt-1">Trades will appear here when executed</div>
          </div>
        ) : (
          <div className="space-y-0">
            {trades.map((trade) => (
              <TradeActivityItem 
                key={trade.id} 
                trade={trade} 
                bot={botMap.get(trade.product_id)}
              />
            ))}
          </div>
        )}
      </div>
    </div>
  );
};

// Helper function for time formatting (moved outside component to avoid recreation)
const formatTime = (timestamp: string) => {
  const now = new Date();
  const time = new Date(timestamp);
  const diffMs = now.getTime() - time.getTime();
  const diffMins = Math.floor(diffMs / (1000 * 60));
  
  if (diffMins < 1) return 'just now';
  if (diffMins < 60) return `${diffMins}m ago`;
  if (diffMins < 1440) return `${Math.floor(diffMins / 60)}h ago`;
  return `${Math.floor(diffMins / 1440)}d ago`;
};

export default EnhancedTradingActivitySection;
