import React from 'react';
import { useSystemStatus } from '../../hooks/useSystemStatus';
import { useEnhancedBotsStatus } from '../../hooks/useBots';
import { DataFreshnessIndicator, PollingStatusIndicator } from '../DataFreshnessIndicators';

interface UnifiedStatusBarProps {
  className?: string;
}

/**
 * Consolidated status bar showing critical system health indicators
 * Designed to be sticky at top with minimal visual impact
 */
export const UnifiedStatusBar: React.FC<UnifiedStatusBarProps> = ({ 
  className = '' 
}) => {
  const { data: systemStatus, isLoading: systemLoading } = useSystemStatus();
  const { data: botsData, dataUpdatedAt, isFetching } = useEnhancedBotsStatus();

  const getSystemHealthColor = () => {
    if (systemLoading || !systemStatus) return 'bg-gray-400';
    
    switch (systemStatus.status) {
      case 'healthy': return 'bg-green-400';
      case 'degraded': return 'bg-yellow-400';
      case 'error': return 'bg-red-400';
      default: return 'bg-gray-400';
    }
  };

  const getSystemHealthText = () => {
    if (systemLoading) return 'Loading...';
    if (!systemStatus) return 'Unknown';
    
    switch (systemStatus.status) {
      case 'healthy': return 'Healthy';
      case 'degraded': return 'Degraded';
      case 'error': return 'Error';
      default: return 'Unknown';
    }
  };

  const activeBotsCount = botsData?.filter(bot => bot.status === 'RUNNING').length || 0;
  const hotBotsCount = botsData?.filter(bot => bot.temperature === 'HOT').length || 0;
  const totalBotsCount = botsData?.length || 0;

  return (
    <div className={`
      sticky top-0 z-50 bg-white border-b border-gray-200 px-4 py-3 shadow-sm
      ${className}
    `}>
      <div className="flex items-center justify-between">
        {/* Left: System Status */}
        <div className="flex items-center space-x-4">
          <div className="flex items-center space-x-2">
            <div className={`w-3 h-3 rounded-full ${getSystemHealthColor()}`}></div>
            <span className="text-sm font-medium text-gray-900">
              {getSystemHealthText()}
            </span>
          </div>

          <div className="text-gray-300">|</div>

          {/* Bots Status */}
          <div className="flex items-center space-x-3 text-sm text-gray-600">
            <span>
              <span className="font-medium text-gray-900">{totalBotsCount}</span> Bots
            </span>
            <span>
              <span className="font-medium text-green-600">{activeBotsCount}</span> Running
            </span>
            {hotBotsCount > 0 && (
              <span>
                <span className="font-medium text-red-600">{hotBotsCount}</span> 🔥 Hot
              </span>
            )}
          </div>
        </div>

        {/* Right: Data Freshness & Polling */}
        <div className="flex items-center space-x-4">
          {/* Market Data Status */}
          {systemStatus?.data_freshness?.market_data && (
            <>
              <div className="flex items-center space-x-1 text-sm text-gray-600">
                <span>Market Data:</span>
                <div className={`w-2 h-2 rounded-full ${
                  systemStatus.data_freshness.market_data.healthy ? 'bg-green-400' : 'bg-red-400'
                }`}></div>
                <span>
                  {systemStatus.data_freshness.market_data.seconds_since_update 
                    ? `${systemStatus.data_freshness.market_data.seconds_since_update}s ago`
                    : 'No data'
                  }
                </span>
              </div>
              <div className="text-gray-300">|</div>
            </>
          )}

          {/* Data Freshness */}
          <DataFreshnessIndicator 
            lastUpdated={new Date(dataUpdatedAt || Date.now())} 
            showTimestamp={true}
            size="sm"
            freshThresholdSeconds={10}
            staleThresholdSeconds={30}
          />

          {/* Polling Status */}
          <PollingStatusIndicator isPolling={!isFetching} interval={5000} />

          {/* Loading Indicator */}
          {isFetching && (
            <div className="flex items-center space-x-1">
              <div className="w-3 h-3 border-2 border-blue-400 border-t-transparent rounded-full animate-spin"></div>
              <span className="text-sm text-blue-600">Refreshing...</span>
            </div>
          )}
        </div>
      </div>

      {/* Error Banner (if system unhealthy) */}
      {systemStatus?.status === 'error' && (
        <div className="mt-2 p-2 bg-red-50 border border-red-200 rounded text-sm text-red-800">
          <span className="font-medium">System Error:</span> {systemStatus.error || 'Unknown error occurred'}
        </div>
      )}

      {/* Degraded Warning (if system degraded) */}
      {systemStatus?.status === 'degraded' && (
        <div className="mt-2 p-2 bg-yellow-50 border border-yellow-200 rounded text-sm text-yellow-800">
          <span className="font-medium">Performance Degraded:</span> Some services may be slower than usual
        </div>
      )}
    </div>
  );
};

export default UnifiedStatusBar;
