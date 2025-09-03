import React from 'react';
import { useWebSocketStable } from '../hooks/useWebSocketStable';

const SimpleTemperatureDashboard: React.FC = () => {
  const { isConnected, dashboardData, lastUpdate, error } = useWebSocketStable();

  if (error) {
    return (
      <div className="bg-red-50 border border-red-200 rounded-lg p-4">
        <div className="flex items-center">
          <div className="flex-shrink-0">
            <span className="text-red-500">❌</span>
          </div>
          <div className="ml-3">
            <h3 className="text-sm font-medium text-red-800">WebSocket Error</h3>
            <div className="mt-2 text-sm text-red-700">
              <p>{error}</p>
            </div>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="bg-white shadow rounded-lg">
      <div className="px-4 py-5 sm:p-6">
        {/* Header */}
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-lg leading-6 font-medium text-gray-900">
            🌡️ Bot Temperature Monitor (Phase 3.3)
          </h3>
          <div className="flex items-center space-x-2">
            <div className={`w-2 h-2 rounded-full ${
              isConnected ? 'bg-green-500' : 'bg-red-500'
            }`}></div>
            <span className="text-sm text-gray-500">
              {isConnected ? 'Connected' : 'Disconnected'}
            </span>
          </div>
        </div>

        {/* Connection Status */}
        {!isConnected && (
          <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-3 mb-4">
            <p className="text-sm text-yellow-800">
              🔄 Connecting to real-time data stream...
            </p>
          </div>
        )}

        {/* Dashboard Data */}
        {dashboardData ? (
          <div className="space-y-4">
            {/* Summary */}
            <div className="grid grid-cols-3 gap-4">
              <div className="text-center">
                <div className="text-2xl font-bold text-blue-600">
                  {dashboardData.total_bots}
                </div>
                <div className="text-sm text-gray-500">Total Bots</div>
              </div>
              <div className="text-center">
                <div className="text-2xl font-bold text-green-600">
                  {dashboardData.running_bots}
                </div>
                <div className="text-sm text-gray-500">Running</div>
              </div>
              <div className="text-center">
                <div className="text-2xl font-bold text-gray-600">
                  {dashboardData.stopped_bots}
                </div>
                <div className="text-sm text-gray-500">Stopped</div>
              </div>
            </div>

            {/* Bot Temperature List */}
            <div className="space-y-2">
              <h4 className="text-sm font-medium text-gray-900">Bot Temperatures</h4>
              {dashboardData.bot_temperatures.map((bot) => (
                <div
                  key={bot.bot_id}
                  className="flex items-center justify-between p-3 bg-gray-50 rounded-lg"
                >
                  <div className="flex items-center space-x-3">
                    <span className="text-2xl">{bot.temperature_emoji}</span>
                    <div>
                      <div className="font-medium text-gray-900">{bot.bot_name}</div>
                      <div className="text-sm text-gray-500">{bot.pair}</div>
                    </div>
                  </div>
                  <div className="text-right">
                    <div className="text-sm font-medium text-gray-900">
                      {bot.temperature.toUpperCase()}
                    </div>
                    <div className="text-xs text-gray-500">
                      {bot.current_action}
                    </div>
                  </div>
                </div>
              ))}
            </div>

            {/* Last Update */}
            {lastUpdate && (
              <div className="text-xs text-gray-500 text-center">
                Last updated: {lastUpdate.toLocaleTimeString()}
              </div>
            )}
          </div>
        ) : (
          <div className="text-center py-8">
            <div className="text-gray-500">
              {isConnected ? '📊 Waiting for data...' : '🔌 Establishing connection...'}
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default SimpleTemperatureDashboard;
