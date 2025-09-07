import React from 'react';
import { useBotPendingOrders } from '../hooks/useBotPendingOrders';

interface BotPendingOrderIndicatorProps {
  botId: number;
  botName?: string;
}

export const BotPendingOrderIndicator: React.FC<BotPendingOrderIndicatorProps> = ({ 
  botId, 
  botName = `Bot ${botId}` 
}) => {
  const { data: pendingOrderStatus, isLoading } = useBotPendingOrders(botId);

  if (isLoading) {
    return (
      <div className="flex items-center space-x-2">
        <div className="w-2 h-2 bg-gray-300 rounded-full animate-pulse"></div>
        <span className="text-xs text-gray-500">Checking orders...</span>
      </div>
    );
  }

  if (!pendingOrderStatus?.hasPendingOrder) {
    return (
      <div className="flex items-center space-x-2">
        <div className="w-2 h-2 bg-green-500 rounded-full"></div>
        <span className="text-xs text-green-600">Ready to trade</span>
      </div>
    );
  }

  const { pendingOrderCount, mostRecentPendingOrder } = pendingOrderStatus;

  return (
    <div className="flex items-center space-x-2">
      <div className="w-2 h-2 bg-yellow-500 rounded-full animate-pulse"></div>
      <span className="text-xs text-yellow-600">
        {pendingOrderCount} pending order{pendingOrderCount > 1 ? 's' : ''}
      </span>
      {mostRecentPendingOrder && (
        <span className="text-xs text-gray-500">
          ({mostRecentPendingOrder.side} order)
        </span>
      )}
    </div>
  );
};

// Alternative: Simple pending order badge
export const PendingOrderBadge: React.FC<{ botId: number }> = ({ botId }) => {
  const { data: pendingOrderStatus } = useBotPendingOrders(botId);

  if (!pendingOrderStatus?.hasPendingOrder) return null;

  return (
    <span className="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-yellow-100 text-yellow-800">
      <div className="w-1.5 h-1.5 bg-yellow-400 rounded-full mr-1 animate-pulse"></div>
      {pendingOrderStatus.pendingOrderCount} pending
    </span>
  );
};
