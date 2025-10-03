import React from 'react';
import { useSystemStatus } from '../../hooks/useSystemStatus';
import { useCacheStats } from '../../hooks/useCacheStats';
import { useEnhancedBotsStatus } from '../../hooks/useBots';
import { DataFreshnessIndicator } from '../DataFreshnessIndicators';
import { Settings } from 'lucide-react';

interface SystemHealthCardProps {
  className?: string;
  onViewDetails?: () => void;
}

/**
 * Compact System Health Card - Fixed sizing and accurate data
 */
export const SystemHealthCard: React.FC<SystemHealthCardProps> = ({ 
  className = '',
  onViewDetails
}) => {
  const { data: systemStatus, isLoading: statusLoading, dataUpdatedAt } = useSystemStatus();
  const { data: cacheStats } = useCacheStats();
  const { data: botsData } = useEnhancedBotsStatus();

  if (statusLoading) {
    return (
      <div className={`bg-white rounded-xl shadow-lg border p-4 animate-pulse ${className}`}>
        <div className="h-6 bg-gray-200 rounded w-1/2 mb-3"></div>
        <div className="h-8 bg-gray-200 rounded w-2/3"></div>
      </div>
    );
  }

  const isHealthy = systemStatus?.status === 'healthy';
  const hitRate = cacheStats?.cache_performance?.cache_hit_rate ?? 0;
  const hasError = cacheStats?.cache_performance?.status === 'error';
  
  // Bot statistics
  const activeBotsCount = botsData?.filter(bot => bot.status === 'RUNNING').length || 0;
  const hotBotsCount = botsData?.filter(bot => bot.temperature === 'HOT').length || 0;
  const totalBotsCount = botsData?.length || 0;

  const getStatusColor = () => {
    if (isHealthy && !hasError) return 'bg-green-50 border-green-200';
    if (isHealthy) return 'bg-yellow-50 border-yellow-200';
    return 'bg-red-50 border-red-200';
  };

  const getStatusIcon = () => {
    if (isHealthy && !hasError) return '🟢';
    if (isHealthy) return '🟡';
    return '🔴';
  };

  const getStatusText = () => {
    if (isHealthy && !hasError) return 'Healthy';
    if (isHealthy) return 'Cache Issues';
    return 'System Error';
  };

  return (
    <div className={`${getStatusColor()} rounded-xl shadow-lg border p-4 ${className}`}>
      {/* Compact Header */}
      <div className="flex items-center justify-between mb-3">
        <div className="flex items-center space-x-2">
          <h3 className="text-lg font-semibold text-gray-900">System Health</h3>
          <span className="text-xl">{getStatusIcon()}</span>
        </div>
        <DataFreshnessIndicator 
          lastUpdated={new Date(dataUpdatedAt || Date.now())}
          size="sm"
          freshThresholdSeconds={15}
          staleThresholdSeconds={30}
        />
      </div>

      {/* Status Line */}
      <div className="mb-3">
        <div className="text-2xl font-bold text-gray-900">{getStatusText()}</div>
      </div>

      {/* Compact Metrics */}
      <div className="grid grid-cols-2 gap-3 mb-3 text-sm">
        <div className="flex justify-between">
          <span className="text-gray-600">Cache:</span>
          <span className={`font-medium ${
            hasError ? 'text-red-600' : 
            hitRate >= 80 ? 'text-green-600' : 'text-yellow-600'
          }`}>
            {hasError ? 'Error' : `${hitRate.toFixed(1)}%`}
          </span>
        </div>
        <div className="flex justify-between">
          <span className="text-gray-600">Services:</span>
          <span className="font-medium text-green-600">
            {systemStatus?.services ? Object.keys(systemStatus.services).length : 0}/3
          </span>
        </div>
        <div className="flex justify-between">
          <span className="text-gray-600">Bots:</span>
          <span className="font-medium text-gray-900">
            {totalBotsCount} total
          </span>
        </div>
        <div className="flex justify-between">
          <span className="text-gray-600">Running:</span>
          <span className="font-medium text-green-600">
            {activeBotsCount}
          </span>
        </div>
        {hotBotsCount > 0 && (
          <div className="flex justify-between col-span-2">
            <span className="text-gray-600">🔥 Hot bots:</span>
            <span className="font-medium text-red-600">
              {hotBotsCount}
            </span>
          </div>
        )}
      </div>

      {/* View Details Button - Compact */}
      {onViewDetails && (
        <button
          onClick={onViewDetails}
          className="w-full flex items-center justify-center space-x-1 px-2 py-1 text-xs font-medium text-blue-600 bg-blue-50 hover:bg-blue-100 rounded-md transition-colors"
        >
          <Settings className="h-3 w-3" />
          <span>Details</span>
        </button>
      )}
    </div>
  );
};

export default SystemHealthCard;
