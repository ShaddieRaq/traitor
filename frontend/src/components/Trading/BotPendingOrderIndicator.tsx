import React from 'react';
import { useBotPendingOrders, useBotPendingOrderDetails } from '../../hooks/useBotPendingOrders';
import { usePendingOrderUpdates } from '../../hooks/usePendingOrderUpdates';

interface BotPendingOrderIndicatorProps {
  botId: number;
  showDetails?: boolean;
  variant?: 'compact' | 'detailed';
}

export const BotPendingOrderIndicator: React.FC<BotPendingOrderIndicatorProps> = ({ 
  botId,
  showDetails = false,
  variant = 'compact'
}) => {
  const { data: pendingOrderStatus, isLoading } = useBotPendingOrders(botId);
  const { data: pendingOrderDetails } = useBotPendingOrderDetails(botId);
  const { getPendingOrdersForBot, hasPendingOrdersForBot } = usePendingOrderUpdates();

  // Get real-time pending orders from WebSocket
  const realtimePendingOrders = getPendingOrdersForBot(botId);
  const hasRealtimePending = hasPendingOrdersForBot(botId);

  // Use real-time data if available, fallback to API data
  const hasPendingOrders = hasRealtimePending || pendingOrderStatus?.hasPendingOrder || false;
  const pendingCount = realtimePendingOrders.length || pendingOrderStatus?.pendingOrderCount || 0;

  if (isLoading) {
    return (
      <div className="flex items-center space-x-2">
        <div className="w-2 h-2 bg-gray-300 rounded-full animate-pulse"></div>
        <span className="text-xs text-gray-500">Checking orders...</span>
      </div>
    );
  }

  if (!hasPendingOrders) {
    return (
      <div className="flex items-center space-x-2">
        <div className="w-2 h-2 bg-green-500 rounded-full"></div>
        <span className="text-xs text-green-600">Ready to trade</span>
      </div>
    );
  }

  // Determine urgency from pending order details
  const criticalCount = pendingOrderDetails?.critical_count || 0;
  const warningCount = pendingOrderDetails?.warning_count || 0;
  const oldestMinutes = pendingOrderDetails?.oldest_pending_minutes || 0;

  const getUrgencyInfo = () => {
    if (criticalCount > 0) {
      return {
        color: 'text-red-600',
        bgColor: 'bg-red-100',
        dotColor: 'bg-red-500',
        urgency: 'critical',
        message: `${criticalCount} stuck order${criticalCount > 1 ? 's' : ''}`
      };
    } else if (warningCount > 0) {
      return {
        color: 'text-yellow-600',
        bgColor: 'bg-yellow-100',
        dotColor: 'bg-yellow-500',
        urgency: 'warning',
        message: `${warningCount} slow order${warningCount > 1 ? 's' : ''}`
      };
    } else {
      return {
        color: 'text-blue-600',
        bgColor: 'bg-blue-100',
        dotColor: 'bg-blue-500',
        urgency: 'normal',
        message: 'processing normally'
      };
    }
  };

  const urgencyInfo = getUrgencyInfo();

  if (variant === 'compact') {
    return (
      <div className="flex items-center space-x-2">
        <div className={`w-2 h-2 ${urgencyInfo.dotColor} rounded-full animate-pulse`}></div>
        <span className={`text-xs ${urgencyInfo.color}`}>
          {pendingCount} pending order{pendingCount > 1 ? 's' : ''}
        </span>
        {realtimePendingOrders.length > 0 && realtimePendingOrders[0] && (
          <span className="text-xs text-gray-500">
            ({realtimePendingOrders[0].side} order)
          </span>
        )}
      </div>
    );
  }

  // Detailed variant
  return (
    <div className={`p-3 rounded-lg border ${urgencyInfo.bgColor} border-opacity-50`}>
      <div className="flex items-center justify-between mb-2">
        <div className="flex items-center space-x-2">
          <div className={`w-2 h-2 ${urgencyInfo.dotColor} rounded-full animate-pulse`}></div>
          <span className={`text-sm font-medium ${urgencyInfo.color}`}>
            {pendingCount} Pending Order{pendingCount > 1 ? 's' : ''}
          </span>
        </div>
        {oldestMinutes > 0 && (
          <span className="text-xs text-gray-500">
            Oldest: {oldestMinutes}m
          </span>
        )}
      </div>

      {showDetails && realtimePendingOrders.length > 0 && (
        <div className="space-y-1">
          {realtimePendingOrders.slice(0, 3).map((order) => (
            <div key={order.order_id} className="flex items-center justify-between text-xs">
              <span className={`font-medium ${order.side === 'BUY' ? 'text-green-600' : 'text-red-600'}`}>
                {order.side} ${order.size_usd.toFixed(2)}
              </span>
              <span className="text-gray-500">
                {Math.floor(order.time_elapsed_seconds / 60)}m {order.time_elapsed_seconds % 60}s
              </span>
            </div>
          ))}
          {realtimePendingOrders.length > 3 && (
            <div className="text-xs text-gray-500 text-center">
              +{realtimePendingOrders.length - 3} more...
            </div>
          )}
        </div>
      )}

      {urgencyInfo.urgency === 'critical' && (
        <div className="mt-2 pt-2 border-t border-red-200">
          <div className="text-xs text-red-700 font-medium">⚠️ Action Required</div>
          <div className="text-xs text-red-600">Orders stuck for 10+ minutes - may need manual sync</div>
        </div>
      )}
    </div>
  );
};

// Alternative: Simple pending order badge
export const PendingOrderBadge: React.FC<{ botId: number }> = ({ botId }) => {
  const { hasPendingOrdersForBot, getPendingOrdersForBot } = usePendingOrderUpdates();
  const { data: pendingOrderStatus } = useBotPendingOrders(botId);

  const hasPendingOrders = hasPendingOrdersForBot(botId) || pendingOrderStatus?.hasPendingOrder || false;
  const pendingCount = getPendingOrdersForBot(botId).length || pendingOrderStatus?.pendingOrderCount || 0;

  if (!hasPendingOrders) return null;

  return (
    <span className="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-yellow-100 text-yellow-800">
      <div className="w-1.5 h-1.5 bg-yellow-400 rounded-full mr-1 animate-pulse"></div>
      {pendingCount} pending
    </span>
  );
};
