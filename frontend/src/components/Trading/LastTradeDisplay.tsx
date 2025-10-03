import React from 'react';
import { LastTradeInfo } from '../../types';

interface LastTradeDisplayProps {
  lastTrade?: LastTradeInfo;
  className?: string;
}

const LastTradeDisplay: React.FC<LastTradeDisplayProps> = ({ lastTrade, className = '' }) => {
  if (!lastTrade) {
    return (
      <div className={`text-xs text-gray-400 ${className}`}>
        No recent trades
      </div>
    );
  }

  const getSideConfig = (side?: string) => {
    switch (side) {
      case 'BUY':
        return { color: 'text-green-600', icon: '↗️', bg: 'bg-green-50' };
      case 'SELL':
        return { color: 'text-red-600', icon: '↘️', bg: 'bg-red-50' };
      default:
        return { color: 'text-gray-600', icon: '↔️', bg: 'bg-gray-50' };
    }
  };

  const getStatusConfig = (status?: string) => {
    switch (status) {
      case 'filled':
        return { color: 'text-green-600', icon: '✅' };
      case 'pending':
        return { color: 'text-yellow-600', icon: '⏳' };
      case 'failed':
        return { color: 'text-red-600', icon: '❌' };
      default:
        return { color: 'text-gray-600', icon: '❓' };
    }
  };

  const getTimeAgoText = (minutesAgo?: number) => {
    if (!minutesAgo) return 'Just now';
    if (minutesAgo < 1) return 'Just now';
    if (minutesAgo < 60) return `${minutesAgo}m ago`;
    const hours = Math.floor(minutesAgo / 60);
    if (hours < 24) return `${hours}h ago`;
    const days = Math.floor(hours / 24);
    return `${days}d ago`;
  };

  const sideConfig = getSideConfig(lastTrade.side);
  const statusConfig = getStatusConfig(lastTrade.status);

  return (
    <div className={`${className}`}>
      <div className="flex items-center justify-between">
        <div className="flex items-center space-x-2">
          <div className={`flex items-center px-1.5 py-0.5 rounded text-xs ${sideConfig.bg} ${sideConfig.color}`}>
            <span className="mr-1">{sideConfig.icon}</span>
            {lastTrade.side}
          </div>
          <span className={`text-xs ${statusConfig.color}`}>
            {statusConfig.icon} {lastTrade.status}
          </span>
        </div>
        <div className="text-xs text-gray-500">
          {getTimeAgoText(lastTrade.minutes_ago)}
        </div>
      </div>
      
      <div className="flex items-center justify-between mt-1 text-xs">
        <div className="text-gray-600">
          ${lastTrade.price?.toLocaleString(undefined, { 
            minimumFractionDigits: 2, 
            maximumFractionDigits: 2 
          })}
        </div>
        <div className="text-gray-500">
          Size: {lastTrade.size?.toFixed(4)}
        </div>
      </div>

      {lastTrade.status === 'pending' && (
        <div className="flex items-center mt-1">
          <div className="w-1 h-1 bg-yellow-400 rounded-full animate-pulse mr-1"></div>
          <span className="text-xs text-yellow-600">
            Waiting for fill...
          </span>
        </div>
      )}
    </div>
  );
};

export default React.memo(LastTradeDisplay);
