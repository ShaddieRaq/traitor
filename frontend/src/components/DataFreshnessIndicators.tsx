import React from 'react';

interface DataFreshnessIndicatorProps {
  lastUpdated: Date;
  freshThresholdSeconds?: number;
  staleThresholdSeconds?: number;
  showTimestamp?: boolean;
  size?: 'sm' | 'md' | 'lg';
}

export const DataFreshnessIndicator: React.FC<DataFreshnessIndicatorProps> = ({
  lastUpdated,
  freshThresholdSeconds = 10,
  staleThresholdSeconds = 30,
  showTimestamp = false,
  size = 'sm'
}) => {
  const now = new Date();
  const secondsAgo = Math.floor((now.getTime() - lastUpdated.getTime()) / 1000);
  
  let status: 'fresh' | 'stale' | 'broken';
  let color: string;
  let pulse: boolean = false;
  
  if (secondsAgo <= freshThresholdSeconds) {
    status = 'fresh';
    color = 'bg-green-400';
    pulse = secondsAgo <= 2; // Pulse for very recent updates
  } else if (secondsAgo <= staleThresholdSeconds) {
    status = 'stale';
    color = 'bg-yellow-400';
  } else {
    status = 'broken';
    color = 'bg-red-400';
  }
  
  const sizeClasses = {
    sm: 'w-2 h-2',
    md: 'w-3 h-3',
    lg: 'w-4 h-4'
  };
  
  const formatTimeAgo = (seconds: number): string => {
    if (seconds < 60) return `${seconds}s ago`;
    if (seconds < 3600) return `${Math.floor(seconds / 60)}m ago`;
    return `${Math.floor(seconds / 3600)}h ago`;
  };
  
  return (
    <div className="flex items-center space-x-1">
      <div className={`
        ${sizeClasses[size]} 
        ${color} 
        rounded-full 
        ${pulse ? 'animate-pulse' : ''}
      `} 
      title={`Data ${status} - Updated ${formatTimeAgo(secondsAgo)}`} 
      />
      {showTimestamp && (
        <span className="text-xs text-gray-500">
          {formatTimeAgo(secondsAgo)}
        </span>
      )}
    </div>
  );
};

interface PollingStatusIndicatorProps {
  isPolling: boolean;
  interval: number;
}

export const PollingStatusIndicator: React.FC<PollingStatusIndicatorProps> = ({
  isPolling,
  interval
}) => {
  return (
    <div className="flex items-center space-x-1" title={`Polling every ${interval / 1000}s`}>
      <div className={`
        w-2 h-2 rounded-full 
        ${isPolling ? 'bg-blue-400 animate-pulse' : 'bg-gray-400'}
      `} />
      <span className="text-xs text-gray-500">
        {isPolling ? `${interval / 1000}s` : 'Paused'}
      </span>
    </div>
  );
};

interface ConnectionStatusIndicatorProps {
  status: 'connected' | 'connecting' | 'disconnected';
  type: string;
  lastActivity?: Date;
}

export const ConnectionStatusIndicator: React.FC<ConnectionStatusIndicatorProps> = ({
  status,
  type,
  lastActivity
}) => {
  const statusConfig = {
    connected: { color: 'bg-green-400', text: 'Connected', pulse: true },
    connecting: { color: 'bg-yellow-400', text: 'Connecting', pulse: true },
    disconnected: { color: 'bg-red-400', text: 'Disconnected', pulse: false }
  };
  
  const config = statusConfig[status];
  
  return (
    <div className="flex items-center space-x-2">
      <div className={`
        w-2 h-2 rounded-full 
        ${config.color} 
        ${config.pulse ? 'animate-pulse' : ''}
      `} />
      <span className="text-xs text-gray-600">
        {type}: {config.text}
      </span>
      {lastActivity && status === 'connected' && (
        <DataFreshnessIndicator 
          lastUpdated={lastActivity} 
          showTimestamp={true}
          size="sm"
        />
      )}
    </div>
  );
};
