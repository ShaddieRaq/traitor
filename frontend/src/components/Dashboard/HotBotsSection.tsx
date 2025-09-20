import React, { useState } from 'react';
import { useEnhancedBotsStatus } from '../../hooks/useBots';
import ExpandableBotCard from './ExpandableBotCard';
import { DataFreshnessIndicator } from '../DataFreshnessIndicators';

interface HotBotsSectionProps {
  className?: string;
}

interface HotBotCardProps {
  bot: any;
}

/**
 * Compact hot bot card with temperature-based styling
 */
const HotBotCard: React.FC<HotBotCardProps> = ({ bot }) => {
  const getTemperatureIcon = () => {
    switch (bot.temperature) {
      case 'HOT': return '🔥';
      case 'WARM': return '🌡️';
      default: return '❄️';
    }
  };

  const getTemperatureStyle = () => {
    switch (bot.temperature) {
      case 'HOT': return 'bg-gradient-to-br from-red-100 to-orange-100 border-red-300';
      case 'WARM': return 'bg-gradient-to-br from-orange-100 to-yellow-100 border-orange-300';
      default: return 'bg-gradient-to-br from-blue-100 to-cyan-100 border-blue-300';
    }
  };

  const getActionIcon = () => {
    if (bot.current_combined_score > 0.1) return '🟢 BUY';
    if (bot.current_combined_score < -0.1) return '🔴 SELL';
    return '🟡 HOLD';
  };

  return (
    <div className={`
      ${getTemperatureStyle()}
      rounded-lg p-4 shadow-lg transform hover:scale-105 transition-transform duration-200
      min-w-[280px] flex-shrink-0 border
    `}>
      {/* Header */}
      <div className="flex items-center justify-between mb-3">
        <div className="flex items-center space-x-2">
          <span className="text-xl">{getTemperatureIcon()}</span>
          <div>
            <div className="font-bold text-gray-900">{bot.pair}</div>
            <div className="text-sm text-gray-600">{bot.name}</div>
          </div>
        </div>
        <span className={`px-2 py-1 rounded text-xs ${
          bot.status === 'RUNNING' ? 'bg-green-100 text-green-800' : 'bg-gray-100 text-gray-600'
        }`}>
          {bot.status}
        </span>
      </div>

      {/* Action Signal */}
      <div className="mb-3">
        <div className="text-lg font-bold">
          {getActionIcon()}
        </div>
        <div className="text-sm text-gray-600">
          Signal: <span className="font-mono">{bot.current_combined_score.toFixed(3)}</span>
        </div>
      </div>

      {/* Signal Strength Indicator */}
      <div className="mb-3">
        <div className="flex items-center justify-between text-xs text-gray-600 mb-1">
          <span>Signal Strength</span>
          <span>{(Math.abs(bot.current_combined_score) * 100).toFixed(1)}%</span>
        </div>
        <div className="w-full bg-gray-200 rounded-full h-2">
          <div 
            className={`h-2 rounded-full transition-all duration-300 ${
              bot.current_combined_score > 0 ? 'bg-green-400' : 'bg-red-400'
            }`}
            style={{ width: `${Math.min(Math.abs(bot.current_combined_score) * 100, 100)}%` }}
          ></div>
        </div>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-2 gap-3 text-sm">
        <div>
          <div className="text-gray-600">Temperature</div>
          <div className="font-semibold">{bot.temperature}</div>
        </div>
        <div>
          <div className="text-gray-600">Distance</div>
          <div className="font-semibold">{bot.distance_to_signal?.toFixed(2) || '--'}</div>
        </div>
      </div>
    </div>
  );
};

/**
 * Horizontal scrolling section for hot/warm bots with temperature-based priority
 */
const HotBotsSection: React.FC<HotBotsSectionProps> = ({ 
  className = '' 
}) => {
  const { data: botsData, isLoading, dataUpdatedAt } = useEnhancedBotsStatus();
  const [viewMode, setViewMode] = useState<'compact' | 'detailed'>('compact');

  if (isLoading) {
    return (
      <div className={`bg-white rounded-lg shadow-lg border p-6 ${className}`}>
        <div className="animate-pulse">
          <div className="h-6 bg-gray-200 rounded w-1/4 mb-4"></div>
          <div className="flex space-x-4 overflow-hidden">
            {[1, 2, 3].map((i) => (
              <div key={i} className="min-w-[280px] h-[180px] bg-gray-200 rounded-lg flex-shrink-0"></div>
            ))}
          </div>
        </div>
      </div>
    );
  }

  // Filter for hot and warm bots
  const hotBots = botsData?.filter(bot => 
    ['HOT', 'WARM'].includes(bot.temperature)
  ) || [];

  // Sort by temperature priority, then by signal strength
  const sortedHotBots = hotBots.sort((a, b) => {
    const tempPriority = { 'HOT': 3, 'WARM': 2, 'COOL': 1, 'FROZEN': 0 };
    const aPriority = tempPriority[a.temperature as keyof typeof tempPriority] || 0;
    const bPriority = tempPriority[b.temperature as keyof typeof tempPriority] || 0;
    
    if (aPriority !== bPriority) {
      return bPriority - aPriority; // Higher priority first
    }
    
    // Same temperature, sort by signal strength
    return Math.abs(b.current_combined_score) - Math.abs(a.current_combined_score);
  });

  if (sortedHotBots.length === 0) {
    return (
      <div className={`bg-white rounded-lg shadow-lg border p-6 ${className}`}>
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-xl font-bold text-gray-900 flex items-center">
            <span className="mr-2">🔥</span>
            Hot Trading Activity
          </h2>
          <DataFreshnessIndicator lastUpdated={new Date(dataUpdatedAt)} />
        </div>
        <div className="text-center py-8 text-gray-500">
          <div className="text-6xl mb-4">❄️</div>
          <p className="text-lg font-medium">All bots are cool right now</p>
          <p className="text-sm">No hot or warm trading signals detected</p>
        </div>
      </div>
    );
  }

  return (
    <div className={`bg-white rounded-lg shadow-lg border ${className}`}>
      {/* Header */}
      <div className="p-6 border-b border-gray-200">
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-xl font-bold text-gray-900 flex items-center">
            <span className="mr-2">🔥</span>
            Hot Trading Activity
            <span className="ml-2 px-2 py-1 bg-red-100 text-red-800 text-sm rounded-full">
              {sortedHotBots.length}
            </span>
          </h2>
          <div className="flex items-center space-x-4">
            <DataFreshnessIndicator lastUpdated={new Date(dataUpdatedAt)} />
            <div className="flex bg-gray-100 rounded-lg p-1">
              <button
                onClick={() => setViewMode('compact')}
                className={`px-3 py-1 rounded text-sm transition-colors ${
                  viewMode === 'compact' 
                    ? 'bg-white text-gray-900 shadow' 
                    : 'text-gray-600 hover:text-gray-900'
                }`}
              >
                Compact
              </button>
              <button
                onClick={() => setViewMode('detailed')}
                className={`px-3 py-1 rounded text-sm transition-colors ${
                  viewMode === 'detailed' 
                    ? 'bg-white text-gray-900 shadow' 
                    : 'text-gray-600 hover:text-gray-900'
                }`}
              >
                Detailed
              </button>
            </div>
          </div>
        </div>

        {/* Temperature Legend */}
        <div className="flex items-center space-x-6 text-sm text-gray-600">
          <div className="flex items-center space-x-1">
            <span>🔥</span>
            <span>HOT (Signal ≥ 0.3)</span>
          </div>
          <div className="flex items-center space-x-1">
            <span>🌡️</span>
            <span>WARM (Signal ≥ 0.15)</span>
          </div>
        </div>
      </div>

      {/* Content */}
      <div className="p-6">
        {viewMode === 'compact' ? (
          <div className="overflow-x-auto">
            <div className="flex space-x-4 pb-2">
              {sortedHotBots.map((bot) => (
                <HotBotCard key={bot.id} bot={bot} />
              ))}
            </div>
          </div>
        ) : (
          <div className="grid grid-cols-1 lg:grid-cols-2 xl:grid-cols-3 gap-6">
            {sortedHotBots.map((bot) => (
              <ExpandableBotCard key={bot.id} bot={bot} />
            ))}
          </div>
        )}
      </div>
    </div>
  );
};

export default HotBotsSection;
