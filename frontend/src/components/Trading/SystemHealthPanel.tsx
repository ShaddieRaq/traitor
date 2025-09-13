import React from 'react';
import { useQuery } from '@tanstack/react-query';

interface SystemError {
  id: string;
  bot_id?: number;
  bot_name?: string;
  error_type: 'signal_calculation' | 'market_data' | 'configuration' | 'trading_logic';
  message: string;
  timestamp: string;
  resolved: boolean;
}

const SystemHealthPanel: React.FC = () => {
  const { data: errors, isLoading } = useQuery<SystemError[]>({
    queryKey: ['system-errors'],
    queryFn: async () => {
      const response = await fetch('/api/v1/system/errors');
      if (!response.ok) throw new Error('Failed to fetch system errors');
      return response.json();
    },
    refetchInterval: 10000, // Check every 10 seconds
  });

  const activeErrors = errors?.filter(e => !e.resolved) || [];
  const recentErrors = errors?.filter(e => e.resolved).slice(0, 3) || [];

  if (isLoading) {
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

  const getErrorIcon = (type: string) => {
    switch (type) {
      case 'signal_calculation': return '📊';
      case 'market_data': return '📡';
      case 'configuration': return '⚙️';
      case 'trading_logic': return '🤖';
      default: return '⚠️';
    }
  };

  const systemStatus = activeErrors.length === 0 ? 'healthy' : 'issues';

  return (
    <div className="mb-6 p-4 bg-white rounded-lg shadow border">
      {/* Header */}
      <div className="flex items-center justify-between mb-4">
        <h2 className="text-lg font-semibold text-gray-900">🔧 System Health</h2>
        <div className={`px-3 py-1 rounded-full border ${
          systemStatus === 'healthy' 
            ? 'bg-green-50 border-green-200 text-green-700' 
            : 'bg-red-50 border-red-200 text-red-700'
        }`}>
          <span className="text-sm font-medium">
            {systemStatus === 'healthy' ? '✅ All Systems Operational' : `⚠️ ${activeErrors.length} Active Issue${activeErrors.length > 1 ? 's' : ''}`}
          </span>
        </div>
      </div>

      {/* Active Errors */}
      {activeErrors.length > 0 && (
        <div className="mb-4">
          <h3 className="text-sm font-medium text-red-700 mb-2">🚨 Active Issues</h3>
          <div className="space-y-2">
            {activeErrors.map((error) => (
              <div key={error.id} className="p-3 bg-red-50 rounded-lg border border-red-200">
                <div className="flex items-start justify-between">
                  <div className="flex-1">
                    <div className="flex items-center mb-1">
                      <span className="mr-2">{getErrorIcon(error.error_type)}</span>
                      <span className="text-sm font-medium text-red-900">
                        {error.bot_name ? `${error.bot_name}: ` : ''}
                        {error.error_type.replace('_', ' ')}
                      </span>
                    </div>
                    <div className="text-sm text-red-800 mb-1">{error.message}</div>
                    <div className="text-xs text-red-600">
                      {new Date(error.timestamp).toLocaleString()}
                    </div>
                  </div>
                  <button className="ml-2 px-2 py-1 text-xs bg-red-100 hover:bg-red-200 rounded border border-red-300">
                    Dismiss
                  </button>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Recent Resolved Errors */}
      {recentErrors.length > 0 && (
        <div>
          <h3 className="text-sm font-medium text-gray-600 mb-2">✅ Recently Resolved</h3>
          <div className="space-y-1">
            {recentErrors.map((error) => (
              <div key={error.id} className="p-2 bg-gray-50 rounded border border-gray-200">
                <div className="flex items-center justify-between">
                  <div className="flex items-center">
                    <span className="mr-2 opacity-60">{getErrorIcon(error.error_type)}</span>
                    <span className="text-sm text-gray-700">
                      {error.bot_name ? `${error.bot_name}: ` : ''}
                      {error.error_type.replace('_', ' ')}
                    </span>
                  </div>
                  <div className="text-xs text-gray-500">
                    {new Date(error.timestamp).toLocaleString()}
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* No Errors State */}
      {activeErrors.length === 0 && recentErrors.length === 0 && (
        <div className="text-center py-4">
          <div className="text-4xl mb-2">🎉</div>
          <div className="text-sm text-gray-600">No system errors detected</div>
          <div className="text-xs text-gray-500 mt-1">All bots are running smoothly</div>
        </div>
      )}
    </div>
  );
};

export default SystemHealthPanel;
