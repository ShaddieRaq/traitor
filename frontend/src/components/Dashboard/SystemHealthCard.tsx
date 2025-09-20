import React from 'react';
import { useSystemStatus } from '../../hooks/useSystemStatus';
import { DataFreshnessIndicator } from '../DataFreshnessIndicators';

interface SystemHealthCardProps {
  className?: string;
}

/**
 * Consolidated system health card showing critical status
 * Designed for 2x2 grid area with clear health indicators
 */
export const SystemHealthCard: React.FC<SystemHealthCardProps> = ({ 
  className = '' 
}) => {
  const { data: systemStatus, isLoading, dataUpdatedAt } = useSystemStatus();

  if (isLoading) {
    return (
      <div className={`
        bg-white rounded-lg shadow-lg border p-6 
        animate-pulse
        ${className}
      `}>
        <div className="space-y-4">
          <div className="h-6 bg-gray-200 rounded w-1/3"></div>
          <div className="h-8 bg-gray-200 rounded w-2/3"></div>
          <div className="grid grid-cols-2 gap-4">
            <div className="h-12 bg-gray-200 rounded"></div>
            <div className="h-12 bg-gray-200 rounded"></div>
          </div>
        </div>
      </div>
    );
  }

  const isHealthy = systemStatus?.status === 'healthy';
  const isDegraded = systemStatus?.status === 'degraded';

  // Determine styling based on system health
  const statusColor = isHealthy ? 'text-green-600' : isDegraded ? 'text-yellow-600' : 'text-red-600';
  const statusBg = isHealthy ? 'bg-green-50 border-green-200' : 
                   isDegraded ? 'bg-yellow-50 border-yellow-200' : 
                   'bg-red-50 border-red-200';
  const statusIcon = isHealthy ? '✅' : isDegraded ? '⚠️' : '❌';
  const statusText = isHealthy ? 'Healthy' : isDegraded ? 'Degraded' : 'Error';

  return (
    <div className={`
      ${statusBg}
      rounded-lg shadow-lg border-2 p-6
      ${className}
    `}>
      {/* Header */}
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center space-x-2">
          <h2 className="text-lg font-semibold text-gray-900">System Health</h2>
          <span className="text-2xl">{statusIcon}</span>
        </div>
        <DataFreshnessIndicator 
          lastUpdated={new Date(dataUpdatedAt || Date.now())}
          size="sm"
          freshThresholdSeconds={15}
          staleThresholdSeconds={30}
        />
      </div>

      {/* Main Status */}
      <div className="mb-6">
        <div className="text-sm text-gray-600 mb-1">Overall Status</div>
        <div className={`text-3xl font-bold ${statusColor}`}>
          {statusText}
        </div>
      </div>

      {/* Key Metrics Grid */}
      <div className="grid grid-cols-2 gap-4 mb-4">
        <div className="text-center p-3 bg-white bg-opacity-50 rounded-lg">
          <div className="text-sm text-gray-600">Polling</div>
          <div className="text-lg font-semibold text-gray-900">
            {systemStatus?.services?.polling?.status === 'active' ? 
              `${systemStatus.services.polling.interval_seconds}s` : 
              'Inactive'
            }
          </div>
        </div>
        <div className="text-center p-3 bg-white bg-opacity-50 rounded-lg">
          <div className="text-sm text-gray-600">Market Data</div>
          <div className="text-lg font-semibold text-gray-900">
            {systemStatus?.data_freshness?.market_data?.healthy ? 
              `${systemStatus.data_freshness.market_data.seconds_since_update}s` : 
              'Stale'
            }
          </div>
        </div>
      </div>

      {/* Service Status Indicators */}
      <div className="pt-4 border-t border-gray-200">
        <div className="text-sm text-gray-600 mb-2">Services</div>
        <div className="flex space-x-4">
          <div className="flex items-center space-x-1">
            <div className={`w-2 h-2 rounded-full ${
              systemStatus?.services?.database?.status === 'healthy' ? 'bg-green-400' : 'bg-red-400'
            }`}></div>
            <span className="text-xs text-gray-600">Database</span>
          </div>
          <div className="flex items-center space-x-1">
            <div className={`w-2 h-2 rounded-full ${
              systemStatus?.services?.polling?.status === 'active' ? 'bg-green-400' : 'bg-red-400'
            }`}></div>
            <span className="text-xs text-gray-600">Polling</span>
          </div>
          <div className="flex items-center space-x-1">
            <div className={`w-2 h-2 rounded-full ${
              systemStatus?.services?.coinbase_api?.status === 'healthy' ? 'bg-green-400' : 'bg-red-400'
            }`}></div>
            <span className="text-xs text-gray-600">Coinbase</span>
          </div>
        </div>
      </div>

      {/* Quick Action */}
      {!isHealthy && (
        <div className="mt-4 pt-4 border-t border-gray-200">
          <button className="text-sm text-blue-600 hover:text-blue-800 underline">
            View Diagnostics →
          </button>
        </div>
      )}
    </div>
  );
};

export default SystemHealthCard;
