import { useState, useEffect } from 'react';
import { useWebSocketTemperature } from '../hooks/useWebSocketTemperature';

interface TempIndicatorProps {
  temperature: string;
  emoji: string;
  botName: string;
  score: number;
  distanceToAction: number;
  isLive?: boolean;
}

const TempIndicator: React.FC<TempIndicatorProps> = ({ 
  temperature, 
  emoji, 
  botName, 
  score, 
  distanceToAction,
  isLive = false 
}) => {
  const [isUpdated, setIsUpdated] = useState(false);

  // Flash effect when data updates
  useEffect(() => {
    if (isLive) {
      setIsUpdated(true);
      const timer = setTimeout(() => setIsUpdated(false), 1000);
      return () => clearTimeout(timer);
    }
  }, [score, temperature, isLive]);

  const getTemperatureColor = (temp: string) => {
    switch (temp) {
      case 'hot':
        return 'bg-red-500 text-white';
      case 'warm':
        return 'bg-orange-500 text-white';
      case 'cool':
        return 'bg-blue-500 text-white';
      case 'frozen':
        return 'bg-gray-500 text-white';
      default:
        return 'bg-gray-400 text-white';
    }
  };

  const getProgressColor = (temp: string) => {
    switch (temp) {
      case 'hot':
        return 'bg-red-200';
      case 'warm':
        return 'bg-orange-200';
      case 'cool':
        return 'bg-blue-200';
      case 'frozen':
        return 'bg-gray-200';
      default:
        return 'bg-gray-200';
    }
  };

  // Calculate progress bar value (inverse of distance to action)
  const progress = Math.max(0, (1 - distanceToAction) * 100);

  return (
    <div className={`p-4 rounded-lg border transition-all duration-300 ${
      isUpdated ? 'ring-2 ring-blue-400 ring-opacity-75 shadow-lg' : 'shadow'
    } bg-white`}>
      <div className="flex items-center justify-between mb-2">
        <h3 className="text-sm font-medium text-gray-900">{botName}</h3>
        {isLive && (
          <div className="flex items-center space-x-1">
            <div className="w-2 h-2 bg-green-500 rounded-full animate-pulse"></div>
            <span className="text-xs text-green-600">Live</span>
          </div>
        )}
      </div>
      
      <div className="flex items-center space-x-3 mb-3">
        <div className={`px-3 py-1 rounded-full text-sm font-medium ${getTemperatureColor(temperature)}`}>
          {emoji} {temperature.charAt(0).toUpperCase() + temperature.slice(1)}
        </div>
        <div className="text-sm text-gray-600">
          Score: {score.toFixed(3)}
        </div>
      </div>
      
      <div className="space-y-2">
        <div className="flex justify-between text-xs text-gray-500">
          <span>Signal Strength</span>
          <span>{progress.toFixed(0)}%</span>
        </div>
        <div className="w-full bg-gray-200 rounded-full h-2">
          <div 
            className={`h-2 rounded-full transition-all duration-500 ${getProgressColor(temperature)}`}
            style={{ width: `${progress}%` }}
          ></div>
        </div>
        <div className="text-xs text-gray-500">
          Distance to action: {distanceToAction.toFixed(3)}
        </div>
      </div>
    </div>
  );
};

const LiveTemperatureDashboard: React.FC = () => {
  const { 
    isConnected, 
    dashboardData, 
    lastUpdate, 
    error, 
    requestUpdate 
  } = useWebSocketTemperature();

  const temperatureBreakdown = dashboardData?.bot_temperatures?.reduce((acc, bot) => {
    acc[bot.temperature] = (acc[bot.temperature] || 0) + 1;
    return acc;
  }, {} as Record<string, number>) || {};

  if (error) {
    return (
      <div className="bg-red-50 border border-red-200 rounded-lg p-4">
        <div className="flex items-center">
          <div className="flex-shrink-0">
            <span className="text-red-400">⚠️</span>
          </div>
          <div className="ml-3">
            <h3 className="text-sm font-medium text-red-800">Connection Error</h3>
            <p className="text-sm text-red-700 mt-1">{error}</p>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Connection Status */}
      <div className="flex items-center justify-between">
        <h2 className="text-lg font-semibold text-gray-900">Live Bot Temperature Monitor</h2>
        <div className="flex items-center space-x-4">
          <div className="flex items-center space-x-2">
            <div className={`w-3 h-3 rounded-full ${isConnected ? 'bg-green-500' : 'bg-red-500'}`}></div>
            <span className="text-sm text-gray-600">
              {isConnected ? 'Connected' : 'Disconnected'}
            </span>
          </div>
          {lastUpdate && (
            <span className="text-xs text-gray-500">
              Last update: {new Date(lastUpdate).toLocaleTimeString()}
            </span>
          )}
          <button
            onClick={requestUpdate}
            className="px-3 py-1 bg-blue-600 text-white text-sm rounded hover:bg-blue-700 transition-colors"
          >
            Refresh
          </button>
        </div>
      </div>

      {/* Summary Stats */}
      {dashboardData && (
        <div className="grid grid-cols-2 md:grid-cols-5 gap-4">
          <div className="bg-white p-4 rounded-lg shadow text-center">
            <div className="text-2xl font-bold text-gray-900">{dashboardData.total_bots}</div>
            <div className="text-sm text-gray-600">Total Bots</div>
          </div>
          <div className="bg-white p-4 rounded-lg shadow text-center">
            <div className="text-2xl font-bold text-green-600">{dashboardData.running_bots}</div>
            <div className="text-sm text-gray-600">Running</div>
          </div>
          <div className="bg-white p-4 rounded-lg shadow text-center">
            <div className="text-2xl font-bold text-red-600">{temperatureBreakdown.hot || 0}</div>
            <div className="text-sm text-gray-600">🔥 Hot</div>
          </div>
          <div className="bg-white p-4 rounded-lg shadow text-center">
            <div className="text-2xl font-bold text-orange-600">{temperatureBreakdown.warm || 0}</div>
            <div className="text-sm text-gray-600">🌡️ Warm</div>
          </div>
          <div className="bg-white p-4 rounded-lg shadow text-center">
            <div className="text-2xl font-bold text-blue-600">{temperatureBreakdown.cool || 0}</div>
            <div className="text-sm text-gray-600">❄️ Cool</div>
          </div>
        </div>
      )}

      {/* Temperature Grid */}
      {dashboardData?.bot_temperatures?.length ? (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {dashboardData.bot_temperatures.map((bot) => (
            <TempIndicator
              key={bot.bot_id}
              temperature={bot.temperature}
              emoji={bot.temperature_emoji}
              botName={bot.bot_name}
              score={bot.score}
              distanceToAction={bot.distance_to_action}
              isLive={isConnected}
            />
          ))}
        </div>
      ) : (
        <div className="text-center py-8">
          <div className="text-gray-500">
            {isConnected ? 'No running bots with temperature data' : 'Connecting...'}
          </div>
        </div>
      )}
    </div>
  );
};

export default LiveTemperatureDashboard;
