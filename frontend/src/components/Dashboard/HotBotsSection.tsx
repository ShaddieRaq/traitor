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
 * Enhanced Hot Bot Card for Phase 2.3 - More prominent design
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
      case 'HOT': return 'bg-gradient-to-br from-red-50 via-red-100 to-orange-100 border-red-400 shadow-red-100';
      case 'WARM': return 'bg-gradient-to-br from-orange-50 via-orange-100 to-yellow-100 border-orange-400 shadow-orange-100';
      default: return 'bg-gradient-to-br from-blue-50 via-blue-100 to-cyan-100 border-blue-400 shadow-blue-100';
    }
  };

  const getActionIcon = () => {
    if (bot.current_combined_score < -0.1) return '🟢 BUY SIGNAL';  // Fixed: Negative = BUY
    if (bot.current_combined_score > 0.1) return '🔴 SELL SIGNAL';  // Fixed: Positive = SELL
    return '🟡 HOLD';
  };

  const getActionStyle = () => {
    if (bot.current_combined_score < -0.1) return 'text-green-700 bg-green-100 border border-green-300';  // Fixed: Negative = BUY (green)
    if (bot.current_combined_score > 0.1) return 'text-red-700 bg-red-100 border border-red-300';      // Fixed: Positive = SELL (red)
    return 'text-yellow-700 bg-yellow-100 border border-yellow-300';
  };

  return (
    <div className={`
      ${getTemperatureStyle()}
      rounded-xl p-5 shadow-xl transform hover:scale-105 transition-all duration-300
      min-w-[320px] flex-shrink-0 border-2 hover:shadow-2xl
    `}>
      {/* Header with enhanced spacing */}
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center space-x-3">
          <span className="text-2xl">{getTemperatureIcon()}</span>
          <div>
            <div className="font-bold text-xl text-gray-900">{bot.pair}</div>
            <div className="text-sm text-gray-600 font-medium">{bot.name}</div>
          </div>
        </div>
        <span className={`px-3 py-1 rounded-full text-xs font-bold ${
          bot.status === 'RUNNING' ? 'bg-green-200 text-green-800' : 'bg-gray-200 text-gray-600'
        }`}>
          {bot.status}
        </span>
      </div>

      {/* Enhanced Action Signal */}
      <div className="mb-4">
        <div className={`text-sm font-bold px-3 py-2 rounded-lg ${getActionStyle()}`}>
          {getActionIcon()}
        </div>
        <div className="text-sm text-gray-700 mt-2">
          Signal Strength: <span className="font-mono font-bold">{bot.current_combined_score.toFixed(3)}</span>
        </div>
      </div>

      {/* Enhanced Signal Strength Indicator */}
      <div className="mb-4">
        <div className="flex items-center justify-between text-sm text-gray-700 mb-2">
          <span className="font-medium">Signal Strength</span>
          <span className="font-bold">{(Math.abs(bot.current_combined_score) * 100).toFixed(1)}%</span>
        </div>
        <div className="w-full bg-gray-300 rounded-full h-3 shadow-inner">
          <div 
            className={`h-3 rounded-full transition-all duration-500 shadow-sm ${
              bot.current_combined_score < 0 ? 'bg-gradient-to-r from-green-400 to-green-500' :   // Fixed: Negative = BUY (green)
              'bg-gradient-to-r from-red-400 to-red-500'                                       // Fixed: Positive = SELL (red)
            }`}
            style={{ width: `${Math.min(Math.abs(bot.current_combined_score) * 100, 100)}%` }}
          ></div>
        </div>
      </div>

      {/* Enhanced Stats Grid */}
      <div className="grid grid-cols-2 gap-4 text-sm">
        <div className="bg-white bg-opacity-60 rounded-lg p-3">
          <div className="text-gray-600 font-medium">Temperature</div>
          <div className="font-bold text-lg">{bot.temperature}</div>
        </div>
        <div className="bg-white bg-opacity-60 rounded-lg p-3">
          <div className="text-gray-600 font-medium">Distance</div>
          <div className="font-bold text-lg">{bot.distance_to_signal?.toFixed(2) || '--'}</div>
        </div>
      </div>
    </div>
  );
};

/**
 * Enhanced Hot Bots Section for Phase 2.3 - 4-column span with prominence
 */
const HotBotsSection: React.FC<HotBotsSectionProps> = ({ 
  className = '' 
}) => {
  const { data: botsData, isLoading, dataUpdatedAt } = useEnhancedBotsStatus();
  const [viewMode, setViewMode] = useState<'compact' | 'detailed'>('compact');

  if (isLoading) {
    return (
      <div className={`bg-white rounded-xl shadow-xl border-2 p-8 ${className}`}>
        <div className="animate-pulse">
          <div className="h-8 bg-gray-200 rounded w-1/4 mb-6"></div>
          <div className="flex space-x-6 overflow-hidden">
            {[1, 2, 3, 4].map((i) => (
              <div key={i} className="min-w-[320px] h-[200px] bg-gray-200 rounded-xl flex-shrink-0"></div>
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

  // Count by temperature for enhanced display
  const hotCount = sortedHotBots.filter(bot => bot.temperature === 'HOT').length;
  const warmCount = sortedHotBots.filter(bot => bot.temperature === 'WARM').length;

  if (sortedHotBots.length === 0) {
    return (
      <div className={`bg-gradient-to-br from-gray-50 to-blue-50 rounded-xl shadow-xl border-2 border-gray-200 p-8 ${className}`}>
        <div className="flex items-center justify-between mb-6">
          <h2 className="text-2xl font-bold text-gray-900 flex items-center">
            <span className="mr-3 text-3xl">🔥</span>
            Hot Trading Activity
          </h2>
          <DataFreshnessIndicator lastUpdated={new Date(dataUpdatedAt)} />
        </div>
        <div className="text-center py-12 text-gray-500">
          <div className="text-8xl mb-6">❄️</div>
          <p className="text-2xl font-bold mb-2">All bots are cool right now</p>
          <p className="text-lg">No hot or warm trading signals detected</p>
        </div>
      </div>
    );
  }

  return (
    <div className={`bg-white rounded-xl shadow-xl border-2 border-gray-200 ${className}`}>
      {/* Enhanced Header */}
      <div className="p-8 border-b border-gray-200 bg-gradient-to-r from-orange-50 to-red-50">
        <div className="flex items-center justify-between mb-6">
          <div className="flex items-center space-x-4">
            <h2 className="text-3xl font-bold text-gray-900 flex items-center">
              <span className="mr-3 text-4xl">🔥</span>
              Hot Trading Activity
            </h2>
            <div className="flex items-center space-x-3">
              {hotCount > 0 && (
                <span className="px-3 py-1 bg-red-200 text-red-800 text-sm font-bold rounded-full">
                  🔥 {hotCount} HOT
                </span>
              )}
              {warmCount > 0 && (
                <span className="px-3 py-1 bg-orange-200 text-orange-800 text-sm font-bold rounded-full">
                  🌡️ {warmCount} WARM
                </span>
              )}
            </div>
          </div>
          <div className="flex items-center space-x-4">
            <DataFreshnessIndicator lastUpdated={new Date(dataUpdatedAt)} />
            <div className="flex bg-gray-100 rounded-lg p-1 shadow-inner">
              <button
                onClick={() => setViewMode('compact')}
                className={`px-4 py-2 rounded-md text-sm font-medium transition-all ${
                  viewMode === 'compact' 
                    ? 'bg-white text-gray-900 shadow-md' 
                    : 'text-gray-600 hover:text-gray-900 hover:bg-gray-50'
                }`}
              >
                Compact View
              </button>
              <button
                onClick={() => setViewMode('detailed')}
                className={`px-4 py-2 rounded-md text-sm font-medium transition-all ${
                  viewMode === 'detailed' 
                    ? 'bg-white text-gray-900 shadow-md' 
                    : 'text-gray-600 hover:text-gray-900 hover:bg-gray-50'
                }`}
              >
                Detailed View
              </button>
            </div>
          </div>
        </div>

        {/* Enhanced Temperature Legend */}
        <div className="flex items-center space-x-8 text-sm text-gray-700 bg-white bg-opacity-60 rounded-lg p-4">
          <div className="flex items-center space-x-2">
            <span className="text-xl">🔥</span>
            <span className="font-medium">HOT: Signal ≥ 0.3 (Ready to trade)</span>
          </div>
          <div className="flex items-center space-x-2">
            <span className="text-xl">🌡️</span>
            <span className="font-medium">WARM: Signal ≥ 0.15 (Building momentum)</span>
          </div>
          <div className="flex items-center space-x-2">
            <span className="text-lg">📊</span>
            <span className="font-medium">Live signals updated every 5 seconds</span>
          </div>
        </div>
      </div>

      {/* Enhanced Content */}
      <div className="p-8">
        {viewMode === 'compact' ? (
          <div className="overflow-x-auto">
            <div className="flex space-x-6 pb-4" style={{ minWidth: 'max-content' }}>
              {sortedHotBots.map((bot) => (
                <HotBotCard key={bot.id} bot={bot} />
              ))}
            </div>
          </div>
        ) : (
          <div className="grid grid-cols-1 lg:grid-cols-2 xl:grid-cols-3 2xl:grid-cols-4 gap-6">
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
