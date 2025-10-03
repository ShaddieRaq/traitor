import React from 'react';
import { useSystemStatus } from '../../hooks/useSystemStatus';
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
  const { data: systemStatus } = useSystemStatus();

  return (
    <div className={`
      sticky top-0 z-50 bg-white border-b border-gray-200 px-4 py-3 shadow-sm
      ${className}
    `}>
      <div className="flex items-center justify-end">
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
            lastUpdated={new Date()}
            showTimestamp={true}
            size="sm"
            freshThresholdSeconds={10}
            staleThresholdSeconds={30}
          />

          {/* Polling Status */}
          <PollingStatusIndicator isPolling={true} interval={5000} />
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
