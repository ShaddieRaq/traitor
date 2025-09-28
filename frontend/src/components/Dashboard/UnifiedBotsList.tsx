import React, { useState } from 'react';
import { useEnhancedBotsStatus } from '../../hooks/useBots';
import { useFilteredBots, countActiveFilters, defaultFilters } from '../../hooks/useFilteredBots';
import AdvancedFilterPanel, { FilterCriteria } from './AdvancedFilterPanel';
import { DataFreshnessIndicator } from '../DataFreshnessIndicators';
import ExpandableBotCard from './ExpandableBotCard';

interface UnifiedBotsListProps {
  className?: string;
}

/**
 * Compact Bot Card for horizontal scrolling view
 */
interface CompactBotCardProps {
  bot: any;
}

const CompactBotCard: React.FC<CompactBotCardProps> = ({ bot }) => {
  const getTemperatureIcon = () => {
    switch (bot.temperature) {
      case 'HOT': return '🔥';
      case 'WARM': return '🌡️';
      case 'COOL': return '❄️';
      default: return '🧊';
    }
  };

  const getTemperatureStyle = () => {
    switch (bot.temperature) {
      case 'HOT': return 'bg-gradient-to-br from-red-50 via-red-100 to-orange-100 border-red-400 shadow-red-100';
      case 'WARM': return 'bg-gradient-to-br from-orange-50 via-orange-100 to-yellow-100 border-orange-400 shadow-orange-100';
      case 'COOL': return 'bg-gradient-to-br from-blue-50 via-blue-100 to-cyan-100 border-blue-400 shadow-blue-100';
      default: return 'bg-gradient-to-br from-gray-50 via-gray-100 to-slate-100 border-gray-400 shadow-gray-100';
    }
  };

  const getActionIcon = () => {
    if (bot.current_combined_score < -0.05) return '🟢 BUY SIGNAL';  // Fixed: Negative = BUY
    if (bot.current_combined_score > 0.05) return '🔴 SELL SIGNAL'; // Fixed: Positive = SELL
    return '🟡 HOLD';
  };

  const getActionStyle = () => {
    if (bot.current_combined_score < -0.05) return 'text-green-700 bg-green-100 border border-green-300'; // Fixed: Negative = BUY (green)
    if (bot.current_combined_score > 0.05) return 'text-red-700 bg-red-100 border border-red-300';   // Fixed: Positive = SELL (red)
    return 'text-yellow-700 bg-yellow-100 border border-yellow-300';
  };

  return (
    <div className={`
      ${getTemperatureStyle()}
      rounded-xl p-5 shadow-xl transform hover:scale-105 transition-all duration-300
      min-w-[320px] flex-shrink-0 border-2 hover:shadow-2xl
    `}>
      {/* Header */}
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

      {/* Action Signal */}
      <div className="mb-4">
        <div className={`text-sm font-bold px-3 py-2 rounded-lg ${getActionStyle()}`}>
          {getActionIcon()}
        </div>
        <div className="text-sm text-gray-700 mt-2">
          Signal Strength: <span className="font-mono font-bold">{bot.current_combined_score.toFixed(3)}</span>
        </div>
      </div>

      {/* Signal Strength Indicator */}
      <div className="mb-4">
        <div className="flex items-center justify-between text-sm text-gray-700 mb-2">
          <span className="font-medium">Signal Strength</span>
          <span className="font-bold">{(Math.abs(bot.current_combined_score) * 100).toFixed(1)}%</span>
        </div>
        <div className="w-full bg-gray-300 rounded-full h-3 shadow-inner">
          <div 
            className={`h-3 rounded-full transition-all duration-500 shadow-sm ${
              bot.current_combined_score < 0 ? 'bg-gradient-to-r from-green-400 to-green-500' :  // Fixed: Negative = BUY (green)
              'bg-gradient-to-r from-red-400 to-red-500'                                          // Fixed: Positive = SELL (red)
            }`}
            style={{ width: `${Math.min(Math.abs(bot.current_combined_score) * 100, 100)}%` }}
          ></div>
        </div>
      </div>

      {/* Stats Grid */}
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
 * Temperature Group Separator Component
 */
const TemperatureGroupSeparator: React.FC<{ 
  temperature: string; 
  count: number; 
  icon: string;
  gradient: string;
}> = ({ temperature, count, icon, gradient }) => (
  <div className={`${gradient} rounded-lg p-4 mb-4 border-2 border-opacity-30`}>
    <div className="flex items-center justify-between">
      <div className="flex items-center space-x-3">
        <span className="text-2xl">{icon}</span>
        <div>
          <h3 className="text-lg font-bold text-gray-900">{temperature} BOTS</h3>
          <p className="text-sm text-gray-600">{count} bot{count !== 1 ? 's' : ''} in this category</p>
        </div>
      </div>
      <div className="text-right">
        <div className="text-2xl font-bold text-gray-700">{count}</div>
      </div>
    </div>
  </div>
);

/**
 * Unified Bots List - Replaces both HotBotsSection and BotGridSection
 * Features:
 * - Shows ALL bots with full expandable details
 * - Groups by temperature with clear separators
 * - Maintains filtering capabilities
 * - Uses ExpandableBotCard for rich information display
 * - Preserves charts, trading intent, performance metrics, and action buttons
 */
const UnifiedBotsList: React.FC<UnifiedBotsListProps> = ({ 
  className = '' 
}) => {
  const { data: botsData, isLoading, dataUpdatedAt } = useEnhancedBotsStatus();
  const [basicFilter, setBasicFilter] = useState<'ALL' | 'HOT' | 'WARM' | 'COOL' | 'FROZEN' | 'RUNNING'>('ALL');
  const [advancedFilters, setAdvancedFilters] = useState<FilterCriteria>(defaultFilters);
  const [showAdvancedFilters, setShowAdvancedFilters] = useState(false);
  const [viewMode, setViewMode] = useState<'compact' | 'detailed'>('detailed');

  // Apply basic filter to advanced filters when basic filter changes
  const handleBasicFilterChange = (filter: typeof basicFilter) => {
    setBasicFilter(filter);
    
    const updatedFilters = { ...advancedFilters };
    updatedFilters.temperature = [];
    updatedFilters.status = [];
    
    switch (filter) {
      case 'HOT':
        updatedFilters.temperature = ['HOT'];
        break;
      case 'WARM':
        updatedFilters.temperature = ['WARM'];
        break;
      case 'COOL':
        updatedFilters.temperature = ['COOL'];
        break;
      case 'FROZEN':
        updatedFilters.temperature = ['FROZEN'];
        break;
      case 'RUNNING':
        updatedFilters.status = ['ACTIVE'];
        break;
      default:
        break;
    }
    
    setAdvancedFilters(updatedFilters);
  };

  const filteredBots = useFilteredBots(botsData || [], advancedFilters);
  const activeFilterCount = countActiveFilters(advancedFilters);

  // Group bots by temperature and sort within groups
  const groupedBots = {
    HOT: filteredBots.filter(bot => bot.temperature === 'HOT').sort((a, b) => 
      Math.abs(b.current_combined_score) - Math.abs(a.current_combined_score)
    ),
    WARM: filteredBots.filter(bot => bot.temperature === 'WARM').sort((a, b) => 
      Math.abs(b.current_combined_score) - Math.abs(a.current_combined_score)
    ),
    COOL: filteredBots.filter(bot => bot.temperature === 'COOL').sort((a, b) => 
      Math.abs(b.current_combined_score) - Math.abs(a.current_combined_score)
    ),
    FROZEN: filteredBots.filter(bot => bot.temperature === 'FROZEN').sort((a, b) => 
      Math.abs(b.current_combined_score) - Math.abs(a.current_combined_score)
    ),
  };

  const handleClearFilters = () => {
    setAdvancedFilters(defaultFilters);
    setBasicFilter('ALL');
  };

  if (isLoading) {
    return (
      <div className={`bg-white rounded-xl shadow-xl border-2 border-gray-200 p-8 ${className}`}>
        <div className="animate-pulse">
          <div className="h-8 bg-gray-200 rounded w-1/3 mb-6"></div>
          <div className="space-y-4">
            {[1, 2, 3, 4, 5].map((i) => (
              <div key={i} className="h-16 bg-gray-200 rounded-lg"></div>
            ))}
          </div>
        </div>
      </div>
    );
  }

  const totalBots = Object.values(groupedBots).flat().length;

  return (
    <div className={`bg-white rounded-xl shadow-xl border-2 border-gray-200 ${className}`}>
      {/* Header with Filters */}
      <div className="p-6 border-b border-gray-200 bg-gradient-to-r from-blue-50 to-indigo-50">
        <div className="flex items-center justify-between mb-6">
          <div className="flex items-center space-x-4">
            <h2 className="text-3xl font-bold text-gray-900 flex items-center tracking-tight">
              <span className="mr-3 text-4xl">🤖</span>
              All Trading Bots
            </h2>
            <span className="px-4 py-2 bg-blue-100 text-blue-800 text-sm font-bold rounded-full border border-blue-200">
              {totalBots} bot{totalBots !== 1 ? 's' : ''} active
            </span>
          </div>
          <div className="flex items-center space-x-4">
            <DataFreshnessIndicator lastUpdated={new Date(dataUpdatedAt)} />
            {/* View Mode Toggle */}
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

        {/* Basic Filter Buttons */}
        <div className="flex flex-wrap gap-2 mb-4">
          {(['ALL', 'HOT', 'WARM', 'COOL', 'FROZEN', 'RUNNING'] as const).map((filter) => (
            <button
              key={filter}
              onClick={() => handleBasicFilterChange(filter)}
              className={`px-4 py-2 rounded-lg text-sm font-medium transition-all duration-200 ${
                basicFilter === filter
                  ? 'bg-blue-600 text-white shadow-lg'
                  : 'bg-white text-gray-700 border border-gray-300 hover:bg-gray-50'
              }`}
            >
              {filter === 'ALL' ? `All (${totalBots})` : 
               filter === 'RUNNING' ? `Running (${filteredBots.filter(b => b.status === 'RUNNING').length})` :
               `${filter} (${groupedBots[filter as keyof typeof groupedBots].length})`}
            </button>
          ))}
        </div>

        {/* View Mode Description */}
        <div className="mb-4 p-3 bg-blue-50 rounded-lg border border-blue-200">
          <div className="flex items-center justify-between text-sm">
            <div className="flex items-center space-x-2">
              <span className="text-blue-600 font-medium">
                {viewMode === 'compact' ? '📊 Compact View:' : '🔍 Detailed View:'}
              </span>
              <span className="text-blue-700">
                {viewMode === 'compact' 
                  ? 'Quick overview cards with horizontal scrolling' 
                  : 'Expandable cards with charts, metrics, and action buttons'
                }
              </span>
            </div>
            <span className="text-xs text-blue-600">
              {viewMode === 'compact' ? 'Click Detailed View for more info' : 'Click any card to expand'}
            </span>
          </div>
        </div>

        {/* Advanced Filter Toggle */}
        <div className="flex items-center justify-between">
          <button
            onClick={() => setShowAdvancedFilters(!showAdvancedFilters)}
            className="text-sm text-blue-600 hover:text-blue-800 font-medium flex items-center space-x-2"
          >
            <span>Advanced Filters</span>
            {activeFilterCount > 0 && (
              <span className="bg-blue-100 text-blue-800 px-2 py-1 rounded-full text-xs font-bold">
                {activeFilterCount}
              </span>
            )}
            <span className={`transform transition-transform ${showAdvancedFilters ? 'rotate-180' : ''}`}>
              ▼
            </span>
          </button>
          
          {activeFilterCount > 0 && (
            <button
              onClick={handleClearFilters}
              className="text-sm text-red-600 hover:text-red-800 font-medium"
            >
              Clear Filters
            </button>
          )}
        </div>

        {/* Advanced Filter Panel */}
        {showAdvancedFilters && (
          <div className="mt-4 p-4 bg-white rounded-lg border border-gray-200">
            <AdvancedFilterPanel
              isOpen={showAdvancedFilters}
              onToggle={() => setShowAdvancedFilters(!showAdvancedFilters)}
              filters={advancedFilters}
              onFiltersChange={setAdvancedFilters}
              onClearFilters={handleClearFilters}
              activeFilterCount={activeFilterCount}
            />
          </div>
        )}
      </div>

      {/* Bot Lists Grouped by Temperature */}
      <div className="p-6">
        {totalBots === 0 ? (
          <div className="text-center py-12 text-gray-500">
            <div className="text-6xl mb-4">🤖</div>
            <p className="text-xl font-bold mb-2">No bots match your filters</p>
            <p className="text-lg">Try adjusting your filter criteria</p>
          </div>
        ) : (
          <div className="space-y-6">
            {/* Render based on view mode */}
            {viewMode === 'compact' ? (
              // Compact View - Horizontal scrolling by temperature groups
              <>
                {/* HOT Bots */}
                {groupedBots.HOT.length > 0 && (
                  <div>
                    <TemperatureGroupSeparator 
                      temperature="HOT" 
                      count={groupedBots.HOT.length} 
                      icon="🔥"
                      gradient="bg-gradient-to-r from-red-50 to-orange-50 border-red-200"
                    />
                    <div className="overflow-x-auto">
                      <div className="flex space-x-4 pb-4" style={{ minWidth: 'max-content' }}>
                        {groupedBots.HOT.map((bot) => (
                          <CompactBotCard key={bot.id} bot={bot} />
                        ))}
                      </div>
                    </div>
                  </div>
                )}

                {/* WARM Bots */}
                {groupedBots.WARM.length > 0 && (
                  <div>
                    <TemperatureGroupSeparator 
                      temperature="WARM" 
                      count={groupedBots.WARM.length} 
                      icon="🌡️"
                      gradient="bg-gradient-to-r from-orange-50 to-yellow-50 border-orange-200"
                    />
                    <div className="overflow-x-auto">
                      <div className="flex space-x-4 pb-4" style={{ minWidth: 'max-content' }}>
                        {groupedBots.WARM.map((bot) => (
                          <CompactBotCard key={bot.id} bot={bot} />
                        ))}
                      </div>
                    </div>
                  </div>
                )}

                {/* COOL Bots */}
                {groupedBots.COOL.length > 0 && (
                  <div>
                    <TemperatureGroupSeparator 
                      temperature="COOL" 
                      count={groupedBots.COOL.length} 
                      icon="❄️"
                      gradient="bg-gradient-to-r from-blue-50 to-cyan-50 border-blue-200"
                    />
                    <div className="overflow-x-auto">
                      <div className="flex space-x-4 pb-4" style={{ minWidth: 'max-content' }}>
                        {groupedBots.COOL.map((bot) => (
                          <CompactBotCard key={bot.id} bot={bot} />
                        ))}
                      </div>
                    </div>
                  </div>
                )}

                {/* FROZEN Bots */}
                {groupedBots.FROZEN.length > 0 && (
                  <div>
                    <TemperatureGroupSeparator 
                      temperature="FROZEN" 
                      count={groupedBots.FROZEN.length} 
                      icon="🧊"
                      gradient="bg-gradient-to-r from-gray-50 to-slate-50 border-gray-200"
                    />
                    <div className="overflow-x-auto">
                      <div className="flex space-x-4 pb-4" style={{ minWidth: 'max-content' }}>
                        {groupedBots.FROZEN.map((bot) => (
                          <CompactBotCard key={bot.id} bot={bot} />
                        ))}
                      </div>
                    </div>
                  </div>
                )}
              </>
            ) : (
              // Detailed View - Expandable cards in vertical layout
              <>
                {/* HOT Bots */}
                {groupedBots.HOT.length > 0 && (
                  <div>
                    <TemperatureGroupSeparator 
                      temperature="HOT" 
                      count={groupedBots.HOT.length} 
                      icon="🔥"
                      gradient="bg-gradient-to-r from-red-50 to-orange-50 border-red-200"
                    />
                    <div className="space-y-3">
                      {groupedBots.HOT.map((bot) => (
                        <ExpandableBotCard key={bot.id} bot={bot} />
                      ))}
                    </div>
                  </div>
                )}

                {/* WARM Bots */}
                {groupedBots.WARM.length > 0 && (
                  <div>
                    <TemperatureGroupSeparator 
                      temperature="WARM" 
                      count={groupedBots.WARM.length} 
                      icon="🌡️"
                      gradient="bg-gradient-to-r from-orange-50 to-yellow-50 border-orange-200"
                    />
                    <div className="space-y-3">
                      {groupedBots.WARM.map((bot) => (
                        <ExpandableBotCard key={bot.id} bot={bot} />
                      ))}
                    </div>
                  </div>
                )}

                {/* COOL Bots */}
                {groupedBots.COOL.length > 0 && (
                  <div>
                    <TemperatureGroupSeparator 
                      temperature="COOL" 
                      count={groupedBots.COOL.length} 
                      icon="❄️"
                      gradient="bg-gradient-to-r from-blue-50 to-cyan-50 border-blue-200"
                    />
                    <div className="space-y-3">
                      {groupedBots.COOL.map((bot) => (
                        <ExpandableBotCard key={bot.id} bot={bot} />
                      ))}
                    </div>
                  </div>
                )}

                {/* FROZEN Bots */}
                {groupedBots.FROZEN.length > 0 && (
                  <div>
                    <TemperatureGroupSeparator 
                      temperature="FROZEN" 
                      count={groupedBots.FROZEN.length} 
                      icon="🧊"
                      gradient="bg-gradient-to-r from-gray-50 to-slate-50 border-gray-200"
                    />
                    <div className="space-y-3">
                      {groupedBots.FROZEN.map((bot) => (
                        <ExpandableBotCard key={bot.id} bot={bot} />
                      ))}
                    </div>
                  </div>
                )}
              </>
            )}
          </div>
        )}
      </div>
    </div>
  );
};

export default UnifiedBotsList;
