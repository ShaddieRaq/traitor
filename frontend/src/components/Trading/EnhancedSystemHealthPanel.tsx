import React, { useState } from 'react';
import { useQuery } from '@tanstack/react-query';

interface SystemError {
  id: string;
  bot_id?: number;
  bot_name?: string;
  error_type: 'signal_calculation' | 'market_data' | 'configuration' | 'trading_logic' | 'system';
  message: string;
  timestamp: string;
  resolved: boolean;
}

interface LogEntry {
  timestamp: string | null;
  level: 'ERROR' | 'WARNING' | 'INFO' | 'DEBUG';
  message: string;
  file: string;
}

interface HealthSummary {
  overall_status: 'healthy' | 'degraded' | 'critical';
  health_score: number;
  services: Record<string, { status: string; details: string }>;
  bots: {
    total_bots: number;
    healthy_bots: number;
    bots_with_issues: number;
    bot_details: Array<{
      id: number;
      name: string;
      status: string;
      signal_locked: boolean;
      health: string;
    }>;
  };
  recent_critical_events: LogEntry[];
  monitoring_active: boolean;
}

const EnhancedSystemHealthPanel: React.FC = () => {
  const [selectedTab, setSelectedTab] = useState<'overview' | 'logs' | 'monitoring'>('overview');
  const [selectedLogFile, setSelectedLogFile] = useState('backend.log');
  
  // System errors query (existing) - Optimized refresh
  const { data: errors, isLoading: errorsLoading, refetch } = useQuery<SystemError[]>({
    queryKey: ['system-errors'],
    queryFn: async () => {
      const response = await fetch('/api/v1/system-errors/errors');
      if (!response.ok) throw new Error('Failed to fetch system errors');
      return response.json();
    },
    refetchInterval: 30000, // Reduced from 10s to 30s
    staleTime: 15000, // Cache for 15 seconds
  });

  // Comprehensive health query (fixed URL and optimized)
  const { data: healthSummary, isLoading: healthLoading } = useQuery<HealthSummary>({
    queryKey: ['health-comprehensive'],
    queryFn: async () => {
      const response = await fetch('/api/v1/health/comprehensive');
      if (!response.ok) throw new Error('Failed to fetch health summary');
      return response.json();
    },
    refetchInterval: 20000, // Reduced from 15s to 20s
    staleTime: 10000, // Cache for 10 seconds
    retry: 2,
  });

  // Recent logs query (fixed URL and optimized)
  const { data: recentLogs, isLoading: logsLoading } = useQuery({
    queryKey: ['health-logs', selectedLogFile],
    queryFn: async () => {
      const response = await fetch(`/api/v1/health/logs?log_file=${selectedLogFile}&lines=50`);
      if (!response.ok) throw new Error('Failed to fetch logs');
      return response.json();
    },
    refetchInterval: selectedTab === 'logs' ? 8000 : false, // Only refresh when logs tab is active, reduced from 5s to 8s
    enabled: selectedTab === 'logs',
    staleTime: 5000,
  });

  // Critical events query (fixed URL and optimized)
  const { data: criticalEvents } = useQuery({
    queryKey: ['health-critical-events'],
    queryFn: async () => {
      const response = await fetch('/api/v1/health/critical-events?minutes=60');
      if (!response.ok) throw new Error('Failed to fetch critical events');
      return response.json();
    },
    refetchInterval: 45000, // Reduced from 30s to 45s
    staleTime: 20000,
  });

  const resolveError = async (errorId: string) => {
    try {
      const response = await fetch(`/api/v1/system-errors/errors/${errorId}/resolve`, {
        method: 'POST',
      });
      if (response.ok) {
        refetch();
      }
    } catch (error) {
      console.error('Failed to resolve error:', error);
    }
  };

  const getHealthStatusColor = (status: string) => {
    switch (status) {
      case 'healthy': return 'text-green-700 bg-green-50 border-green-200';
      case 'degraded': return 'text-yellow-700 bg-yellow-50 border-yellow-200';
      case 'critical': return 'text-red-700 bg-red-50 border-red-200';
      default: return 'text-gray-700 bg-gray-50 border-gray-200';
    }
  };

  const getLogLevelColor = (level: string) => {
    switch (level) {
      case 'ERROR': return 'text-red-600 bg-red-50';
      case 'WARNING': return 'text-yellow-600 bg-yellow-50';
      case 'INFO': return 'text-blue-600 bg-blue-50';
      case 'DEBUG': return 'text-gray-600 bg-gray-50';
      default: return 'text-gray-600 bg-gray-50';
    }
  };

  const formatTimestamp = (timestamp: string | null) => {
    if (!timestamp) return 'N/A';
    try {
      return new Date(timestamp).toLocaleTimeString();
    } catch {
      return timestamp;
    }
  };

  const activeErrors = errors?.filter(e => !e.resolved) || [];
  
  // Only show initial loading, not on refreshes to prevent UI from becoming unreadable
  const isInitialLoading = (errorsLoading && !errors) || (healthLoading && !healthSummary);

  if (isInitialLoading) {
    return (
      <div className="mb-6 p-4 bg-white rounded-lg shadow border animate-pulse">
        <div className="h-6 bg-gray-200 rounded mb-4"></div>
        <div className="space-y-2">
          <div className="h-4 bg-gray-200 rounded"></div>
          <div className="h-4 bg-gray-200 rounded w-3/4"></div>
        </div>
      </div>
    );
  }

  return (
    <div className="mb-6 p-4 bg-white rounded-lg shadow border">
      {/* Header with Status */}
      <div className="flex items-center justify-between mb-4">
        <h2 className="text-lg font-semibold text-gray-900">🔧 System Health Monitor</h2>
        <div className="flex items-center space-x-3">
          {healthSummary && (
            <div className={`px-3 py-1 rounded-full border ${getHealthStatusColor(healthSummary.overall_status)}`}>
              <span className="text-sm font-medium">
                {healthSummary.overall_status === 'healthy' ? '✅' : 
                 healthSummary.overall_status === 'degraded' ? '⚠️' : '🚨'} 
                {healthSummary.overall_status.charAt(0).toUpperCase() + healthSummary.overall_status.slice(1)}
                {healthSummary.health_score !== undefined && ` (${Math.round(healthSummary.health_score * 100)}%)`}
              </span>
            </div>
          )}
          {healthSummary?.monitoring_active && (
            <div className="px-2 py-1 text-xs bg-green-100 text-green-700 rounded">
              🔍 Monitoring Active
            </div>
          )}
          {/* Show subtle refresh indicators */}
          {(healthLoading || errorsLoading) && (
            <div className="w-2 h-2 bg-blue-500 rounded-full animate-pulse"></div>
          )}
        </div>
      </div>

      {/* Tab Navigation */}
      <div className="flex space-x-1 mb-4 border-b">
        {[
          { id: 'overview', label: '📊 Overview', count: activeErrors.length },
          { id: 'logs', label: '📝 Live Logs', count: 0 },
          { id: 'monitoring', label: '🏥 Health Status', count: criticalEvents?.critical_events_count || 0 }
        ].map((tab) => (
          <button
            key={tab.id}
            onClick={() => setSelectedTab(tab.id as any)}
            className={`px-3 py-2 text-sm font-medium rounded-t-lg ${
              selectedTab === tab.id
                ? 'bg-blue-50 text-blue-700 border-b-2 border-blue-500'
                : 'text-gray-500 hover:text-gray-700'
            }`}
          >
            {tab.label}
            {tab.count > 0 && (
              <span className="ml-1 px-1.5 py-0.5 text-xs bg-red-100 text-red-700 rounded-full">
                {tab.count}
              </span>
            )}
          </button>
        ))}
      </div>

      {/* Tab Content */}
      {selectedTab === 'overview' && (
        <div className="space-y-4">
          {/* Active Errors */}
          {activeErrors.length > 0 && (
            <div>
              <h3 className="text-sm font-medium text-red-700 mb-2">🚨 Active Issues</h3>
              <div className="space-y-2">
                {activeErrors.map((error) => (
                  <div key={error.id} className="p-3 bg-red-50 rounded-lg border border-red-200">
                    <div className="flex items-start justify-between">
                      <div className="flex-1">
                        <div className="flex items-center mb-1">
                          <span className="text-sm font-medium text-red-900">
                            {error.bot_name ? `${error.bot_name}: ` : ''}
                            {error.message.toLowerCase().includes('rate limit') ? 'Rate Limiting' : error.error_type.replace('_', ' ')}
                          </span>
                        </div>
                        <div className="text-sm text-red-800 mb-1">{error.message}</div>
                        <div className="text-xs text-red-600">
                          {new Date(error.timestamp).toLocaleString()}
                        </div>
                      </div>
                      <button 
                        onClick={() => resolveError(error.id)}
                        className="ml-2 px-2 py-1 text-xs bg-red-100 hover:bg-red-200 rounded border border-red-300"
                      >
                        Dismiss
                      </button>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Recent Critical Events */}
          {criticalEvents?.events?.length > 0 && (
            <div>
              <h3 className="text-sm font-medium text-yellow-700 mb-2">⚠️ Recent Critical Events</h3>
              <div className="space-y-1 max-h-48 overflow-y-auto">
                {criticalEvents.events.slice(0, 5).map((event: LogEntry, index: number) => (
                  <div key={index} className={`p-2 rounded text-xs ${getLogLevelColor(event.level)}`}>
                    <div className="flex items-center justify-between">
                      <span className="font-mono text-xs truncate flex-1">{event.message}</span>
                      <span className="ml-2 text-xs opacity-70">
                        {formatTimestamp(event.timestamp)} • {event.file}
                      </span>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* No Issues State */}
          {activeErrors.length === 0 && (!criticalEvents?.events?.length) && (
            <div className="text-center py-4">
              <div className="text-4xl mb-2">🎉</div>
              <div className="text-sm text-gray-600">All systems operational</div>
              <div className="text-xs text-gray-500 mt-1">No errors or critical events detected</div>
            </div>
          )}
        </div>
      )}

      {selectedTab === 'logs' && (
        <div className="space-y-4">
          {/* Log File Selector */}
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-2">
              <label className="text-sm font-medium text-gray-700">Log File:</label>
              <select
                value={selectedLogFile}
                onChange={(e) => setSelectedLogFile(e.target.value)}
                className="border rounded px-2 py-1 text-sm"
              >
                <option value="backend.log">Backend (API)</option>
                <option value="celery-worker.log">Celery Worker</option>
                <option value="celery-beat.log">Celery Beat</option>
                <option value="frontend.log">Frontend</option>
              </select>
            </div>
            {logsLoading && (
              <div className="flex items-center space-x-1 text-xs text-gray-500">
                <div className="w-1 h-1 bg-blue-500 rounded-full animate-pulse"></div>
                <span>Refreshing...</span>
              </div>
            )}
          </div>

          {/* Live Log Display */}
          <div className="bg-black rounded p-3 max-h-96 overflow-y-auto">
            <div className="font-mono text-xs space-y-1">
              {recentLogs?.logs?.length > 0 ? (
                recentLogs.logs.map((log: LogEntry, index: number) => (
                  <div key={index} className={`${
                    log.level === 'ERROR' ? 'text-red-400' :
                    log.level === 'WARNING' ? 'text-yellow-400' :
                    log.level === 'INFO' ? 'text-green-400' :
                    'text-gray-400'
                  }`}>
                    <span className="text-gray-500">[{formatTimestamp(log.timestamp)}]</span>
                    <span className="ml-2">{log.message}</span>
                  </div>
                ))
              ) : logsLoading ? (
                <div className="text-gray-500">Loading logs...</div>
              ) : (
                <div className="text-gray-500">No logs available for {selectedLogFile}</div>
              )}
            </div>
          </div>
        </div>
      )}

      {selectedTab === 'monitoring' && healthSummary && (
        <div className="space-y-4">
          {/* Services Status */}
          <div>
            <h3 className="text-sm font-medium text-gray-700 mb-2">🔧 Services Status</h3>
            <div className="grid grid-cols-2 gap-2">
              {Object.entries(healthSummary.services).map(([service, status]) => (
                <div key={service} className="p-2 border rounded">
                  <div className="flex items-center justify-between">
                    <span className="text-sm font-medium capitalize">{service.replace('_', ' ')}</span>
                    <span className={`px-2 py-1 rounded text-xs ${
                      status.status === 'healthy' ? 'bg-green-100 text-green-700' :
                      status.status === 'stale' ? 'bg-yellow-100 text-yellow-700' :
                      'bg-red-100 text-red-700'
                    }`}>
                      {status.status}
                    </span>
                  </div>
                  <div className="text-xs text-gray-600 mt-1">{status.details}</div>
                </div>
              ))}
            </div>
          </div>

          {/* Bots Status */}
          <div>
            <h3 className="text-sm font-medium text-gray-700 mb-2">🤖 Bots Status</h3>
            <div className="p-3 bg-gray-50 rounded">
              <div className="flex items-center justify-between mb-2">
                <span className="text-sm">Total Bots: {healthSummary.bots.total_bots}</span>
                <span className="text-sm">Healthy: {healthSummary.bots.healthy_bots}</span>
              </div>
              {healthSummary.bots.bot_details.map((bot) => (
                <div key={bot.id} className="flex items-center justify-between py-1 text-sm">
                  <span>{bot.name}</span>
                  <div className="flex items-center space-x-2">
                    <span className={`px-2 py-1 rounded text-xs ${
                      bot.health === 'healthy' ? 'bg-green-100 text-green-700' : 'bg-red-100 text-red-700'
                    }`}>
                      {bot.status}
                    </span>
                    {bot.signal_locked && (
                      <span className="text-xs text-red-600">🔒 Signal Locked</span>
                    )}
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default EnhancedSystemHealthPanel;
