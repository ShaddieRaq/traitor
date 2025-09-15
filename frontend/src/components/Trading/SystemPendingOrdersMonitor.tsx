import React from 'react';
import { useSystemPendingOrders } from '../../hooks/useBotPendingOrders';
import { usePendingOrderUpdates } from '../../hooks/usePendingOrderUpdates';

interface SystemPendingOrdersProps {
  className?: string;
  variant?: 'compact' | 'detailed';
}

export const SystemPendingOrdersMonitor: React.FC<SystemPendingOrdersProps> = ({
  className = '',
  variant = 'compact'
}) => {
  const { data: systemPendingData, isLoading } = useSystemPendingOrders();
  const { 
    getPendingOrderCount, 
    getRecentStatusChanges, 
    isConnected 
  } = usePendingOrderUpdates();

  // Use real-time data if available, fallback to API data
  const realtimePendingCount = getPendingOrderCount();
  const recentStatusChanges = getRecentStatusChanges(5);
  
  const totalPending = realtimePendingCount || systemPendingData?.total_pending_orders || 0;
  const criticalOrders = systemPendingData?.critical_orders || 0;
  const warningOrders = systemPendingData?.warning_orders || 0;
  const systemHealth = systemPendingData?.system_health || 'unknown';

  if (isLoading) {
    return (
      <div className={`p-3 bg-gray-50 rounded-lg ${className}`}>
        <div className="flex items-center space-x-2">
          <div className="w-2 h-2 bg-gray-300 rounded-full animate-pulse"></div>
          <span className="text-sm text-gray-500">Checking system orders...</span>
        </div>
      </div>
    );
  }

  const getSystemHealthInfo = () => {
    switch (systemHealth) {
      case 'critical':
        return {
          color: 'text-red-700',
          bgColor: 'bg-red-100',
          borderColor: 'border-red-200',
          icon: '🚨',
          message: 'Critical Issues Detected'
        };
      case 'warning':
        return {
          color: 'text-yellow-700',
          bgColor: 'bg-yellow-100',
          borderColor: 'border-yellow-200',
          icon: '⚠️',
          message: 'Some Orders Delayed'
        };
      case 'normal':
        return {
          color: 'text-blue-700',
          bgColor: 'bg-blue-100',
          borderColor: 'border-blue-200',
          icon: '🔄',
          message: 'Orders Processing'
        };
      case 'healthy':
        return {
          color: 'text-green-700',
          bgColor: 'bg-green-100',
          borderColor: 'border-green-200',
          icon: '✅',
          message: 'All Systems Healthy'
        };
      default:
        return {
          color: 'text-gray-700',
          bgColor: 'bg-gray-100',
          borderColor: 'border-gray-200',
          icon: '📊',
          message: 'System Status Unknown'
        };
    }
  };

  const healthInfo = getSystemHealthInfo();

  if (variant === 'compact') {
    return (
      <div className={`flex items-center space-x-3 p-2 rounded ${healthInfo.bgColor} ${className}`}>
        <div className="flex items-center space-x-1">
          <span className="text-sm">{healthInfo.icon}</span>
          <span className={`text-xs ${healthInfo.color}`}>
            {totalPending > 0 ? `${totalPending} pending` : 'No pending orders'}
          </span>
        </div>
        {!isConnected && (
          <div className="flex items-center space-x-1">
            <div className="w-1 h-1 bg-red-400 rounded-full"></div>
            <span className="text-xs text-red-600">Offline</span>
          </div>
        )}
        {isConnected && (
          <div className="flex items-center space-x-1">
            <div className="w-1 h-1 bg-green-400 rounded-full animate-pulse"></div>
            <span className="text-xs text-green-600">Live</span>
          </div>
        )}
      </div>
    );
  }

  // Detailed variant
  return (
    <div className={`p-4 rounded-lg border ${healthInfo.bgColor} ${healthInfo.borderColor} ${className}`}>
      <div className="flex items-center justify-between mb-3">
        <div className="flex items-center space-x-2">
          <span className="text-lg">{healthInfo.icon}</span>
          <span className={`text-sm font-medium ${healthInfo.color}`}>
            {healthInfo.message}
          </span>
        </div>
        <div className="flex items-center space-x-2">
          {isConnected ? (
            <div className="flex items-center space-x-1">
              <div className="w-2 h-2 bg-green-500 rounded-full animate-pulse"></div>
              <span className="text-xs text-green-600">Live Updates</span>
            </div>
          ) : (
            <div className="flex items-center space-x-1">
              <div className="w-2 h-2 bg-red-500 rounded-full"></div>
              <span className="text-xs text-red-600">Offline</span>
            </div>
          )}
        </div>
      </div>

      {totalPending > 0 && (
        <div className="grid grid-cols-3 gap-4 mb-3">
          <div className="text-center">
            <div className="text-lg font-bold text-gray-900">{totalPending}</div>
            <div className="text-xs text-gray-500">Total Pending</div>
          </div>
          {warningOrders > 0 && (
            <div className="text-center">
              <div className="text-lg font-bold text-yellow-600">{warningOrders}</div>
              <div className="text-xs text-gray-500">Slow Orders</div>
            </div>
          )}
          {criticalOrders > 0 && (
            <div className="text-center">
              <div className="text-lg font-bold text-red-600">{criticalOrders}</div>
              <div className="text-xs text-gray-500">Stuck Orders</div>
            </div>
          )}
        </div>
      )}

      {recentStatusChanges.length > 0 && (
        <div className="border-t pt-3">
          <div className="text-xs font-medium text-gray-700 mb-2">Recent Activity</div>
          <div className="space-y-1">
            {recentStatusChanges.slice(0, 3).map((change, index) => (
              <div key={`${change.order_id}-${index}`} className="flex items-center justify-between text-xs">
                <span className={`font-medium ${change.side === 'BUY' ? 'text-green-600' : 'text-red-600'}`}>
                  {change.side} ${change.size_usd.toFixed(2)}
                </span>
                <span className={`${change.new_status === 'completed' ? 'text-green-600' : 'text-red-600'}`}>
                  {change.new_status === 'completed' ? '✅ Filled' : '❌ Failed'}
                </span>
                <span className="text-gray-500">
                  {new Date(change.timestamp).toLocaleTimeString()}
                </span>
              </div>
            ))}
          </div>
        </div>
      )}

      {criticalOrders > 0 && (
        <div className="mt-3 p-2 bg-red-50 border border-red-200 rounded">
          <div className="text-xs font-medium text-red-700">⚠️ Manual Intervention Needed</div>
          <div className="text-xs text-red-600 mt-1">
            {criticalOrders} order{criticalOrders > 1 ? 's' : ''} stuck for 10+ minutes. 
            Consider using manual sync API.
          </div>
        </div>
      )}
    </div>
  );
};

export default SystemPendingOrdersMonitor;
