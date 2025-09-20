import React from 'react';
import { useSystemStatus } from '../../hooks/useSystemStatus';
import { useCacheStats } from '../../hooks/useCacheStats';
import { DataFreshnessIndicator } from '../DataFreshnessIndicators';

interface SystemHealthCardProps {
  className?: string;
}

/**
 * Enhanced System Health Card for Phase 2.2 - Grid Layout
 * Designed for 2-column span with prominent cache performance and service status
 */
export const SystemHealthCard: React.FC<SystemHealthCardProps> = ({ 
  className = '' 
}) => {
  const { data: systemStatus, isLoading: statusLoading, dataUpdatedAt } = useSystemStatus();
  const { data: cacheStats } = useCacheStats();

  // Only show loading if system status is loading (cache is optional)
  const isLoading = statusLoading;

  // Show loading state while system status is loading
  if (isLoading) {
    return (
      <div className={`
        bg-white rounded-xl shadow-lg border p-6 
        animate-pulse col-span-2
        ${className}
      `}>
        <div className="space-y-4">
          <div className="h-6 bg-gray-200 rounded w-1/3"></div>
          <div className="h-12 bg-gray-200 rounded w-2/3"></div>
          <div className="grid grid-cols-3 gap-4">
            <div className="h-16 bg-gray-200 rounded"></div>
            <div className="h-16 bg-gray-200 rounded"></div>
            <div className="h-16 bg-gray-200 rounded"></div>
          </div>
        </div>
      </div>
    );
  }

  const isHealthy = systemStatus?.status === 'healthy';
  const isDegraded = systemStatus?.status === 'degraded';
  
  // Cache performance metrics with better fallbacks
  const hitRate = cacheStats?.cache_stats?.hit_rate_percent ?? 0;
  const apiCallsSaved = cacheStats?.cache_stats?.api_calls_saved ?? 0;
  const cacheHealth = cacheStats?.performance_analysis?.cache_health ?? 'unknown';

  // Determine overall system styling with enhanced gradients
  const getSystemGradient = () => {
    if (isHealthy && hitRate >= 85) {
      return 'bg-gradient-to-br from-green-50 via-emerald-50 to-green-100 border-green-300';
    } else if (isHealthy || isDegraded) {
      return 'bg-gradient-to-br from-yellow-50 via-amber-50 to-yellow-100 border-yellow-300';
    } else {
      return 'bg-gradient-to-br from-red-50 via-rose-50 to-red-100 border-red-300';
    }
  };

  const getStatusIcon = () => {
    if (isHealthy && hitRate >= 85) return '🟢';
    if (isHealthy || isDegraded) return '🟡';
    return '🔴';
  };

  const getStatusText = () => {
    if (isHealthy && hitRate >= 85) return 'Excellent';
    if (isHealthy) return 'Healthy';
    if (isDegraded) return 'Degraded';
    return 'Error';
  };

  return (
    <div className={`
      ${getSystemGradient()}
      rounded-xl shadow-lg border-2 p-6 col-span-2
      ${className}
    `}>
      {/* Header with enhanced spacing */}
      <div className="flex items-center justify-between mb-6">
        <div className="flex items-center space-x-3">
          <h2 className="text-xl font-bold text-gray-900">System Health</h2>
          <span className="text-3xl">{getStatusIcon()}</span>
        </div>
        <DataFreshnessIndicator 
          lastUpdated={new Date(dataUpdatedAt || Date.now())}
          size="sm"
          freshThresholdSeconds={15}
          staleThresholdSeconds={30}
        />
      </div>

      {/* Main Status with enhanced typography */}
      <div className="mb-8">
        <div className="text-sm font-medium text-gray-600 mb-2">Overall Status</div>
        <div className="text-4xl font-bold text-gray-900">
          {getStatusText()}
        </div>
      </div>

      {/* Enhanced Performance Metrics Grid */}
      <div className="grid grid-cols-3 gap-6 mb-6">
        {/* Cache Performance */}
        <div className="text-center p-4 bg-white bg-opacity-60 rounded-lg">
          <div className="text-sm font-medium text-gray-600">Cache Hit Rate</div>
          <div className={`text-2xl font-bold ${
            hitRate >= 90 ? 'text-green-600' : 
            hitRate >= 80 ? 'text-yellow-600' : 'text-red-600'
          }`}>
            {hitRate.toFixed(1)}%
          </div>
        </div>

        {/* API Calls Saved */}
        <div className="text-center p-4 bg-white bg-opacity-60 rounded-lg">
          <div className="text-sm font-medium text-gray-600">API Savings</div>
          <div className="text-2xl font-bold text-blue-600">
            {apiCallsSaved}
          </div>
        </div>

        {/* Service Count */}
        <div className="text-center p-4 bg-white bg-opacity-60 rounded-lg">
          <div className="text-sm font-medium text-gray-600">Services</div>
          <div className={`text-2xl font-bold ${
            systemStatus?.services ? 'text-green-600' : 'text-red-600'
          }`}>
            {systemStatus?.services ? Object.keys(systemStatus.services).length : 0}/3
          </div>
        </div>
      </div>

      {/* Enhanced Service Status Indicators */}
      <div className="pt-4 border-t border-gray-200">
        <div className="text-sm font-medium text-gray-600 mb-3">Service Status</div>
        <div className="flex justify-between">
          <div className="flex items-center space-x-2">
            <div className={`w-3 h-3 rounded-full ${
              systemStatus?.services?.database?.status === 'healthy' ? 'bg-green-400' : 'bg-red-400'
            }`}></div>
            <span className="text-sm font-medium text-gray-700">Database</span>
          </div>
          <div className="flex items-center space-x-2">
            <div className={`w-3 h-3 rounded-full ${
              systemStatus?.services?.coinbase_api?.status === 'healthy' ? 'bg-green-400' : 'bg-red-400'
            }`}></div>
            <span className="text-sm font-medium text-gray-700">Coinbase API</span>
          </div>
          <div className="flex items-center space-x-2">
            <div className={`w-3 h-3 rounded-full ${
              systemStatus?.services?.polling?.status === 'active' ? 'bg-green-400' : 'bg-red-400'
            }`}></div>
            <span className="text-sm font-medium text-gray-700">Polling</span>
          </div>
        </div>
      </div>

      {/* Cache Health Indicator */}
      {cacheHealth && (
        <div className="mt-4 pt-4 border-t border-gray-200">
          <div className="flex items-center justify-between">
            <span className="text-sm font-medium text-gray-600">Cache Health</span>
            <span className={`text-sm font-bold capitalize ${
              cacheHealth === 'excellent' ? 'text-green-600' : 
              cacheHealth === 'good' ? 'text-yellow-600' : 'text-red-600'
            }`}>
              {cacheHealth}
            </span>
          </div>
        </div>
      )}
    </div>
  );
};

export default SystemHealthCard;
