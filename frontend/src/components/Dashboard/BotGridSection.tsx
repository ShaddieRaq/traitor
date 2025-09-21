import React, { useState } from 'react';
import { useEnhancedBotsStatus } from '../../hooks/useBots';
import { useFilteredBots, countActiveFilters, defaultFilters } from '../../hooks/useFilteredBots';
import AdvancedFilterPanel, { FilterCriteria } from './AdvancedFilterPanel';
import { DataFreshnessIndicator } from '../DataFreshnessIndicators';

interface BotGridSectionProps {
  className?: string;
}

interface CompactBotCardProps {
  bot: any;
}

/**
 * Enhanced Compact Bot Card for Phase 2.4 - Professional grid display
 */
const CompactBotCard: React.FC<CompactBotCardProps> = ({ bot }) => {
  const getTemperatureColor = () => {
    switch (bot.temperature) {
      case 'HOT': return 'border-red-300 bg-gradient-to-br from-red-50 to-orange-50 shadow-red-100';
      case 'WARM': return 'border-orange-300 bg-gradient-to-br from-orange-50 to-yellow-50 shadow-orange-100';
      case 'COOL': return 'border-blue-300 bg-gradient-to-br from-blue-50 to-cyan-50 shadow-blue-100';
      default: return 'border-gray-300 bg-gradient-to-br from-gray-50 to-slate-50 shadow-gray-100';
    }
  };

  const getTemperatureIcon = () => {
    switch (bot.temperature) {
      case 'HOT': return '🔥';
      case 'WARM': return '🌡️';
      case 'COOL': return '❄️';
      default: return '🧊';
    }
  };

  const getActionText = () => {
    if (bot.current_combined_score < -0.1) return 'BUY';  // Fixed: Negative = BUY
    if (bot.current_combined_score > 0.1) return 'SELL';  // Fixed: Positive = SELL
    return 'HOLD';
  };

  const getActionBadge = () => {
    if (bot.current_combined_score < -0.1) return 'bg-green-100 text-green-800 border-green-300';  // Fixed: Negative = BUY (green)
    if (bot.current_combined_score > 0.1) return 'bg-red-100 text-red-800 border-red-300';      // Fixed: Positive = SELL (red)
    return 'bg-gray-100 text-gray-700 border-gray-300';
  };

  return (
    <div className={`
      ${getTemperatureColor()}
      rounded-xl border-2 p-5 hover:shadow-xl transition-all duration-300 transform hover:scale-105
      h-[200px] flex flex-col justify-between shadow-lg
    `}>
      {/* Enhanced Header */}
      <div className="flex items-center justify-between mb-3">
        <div>
          <div className="font-bold text-gray-900 text-lg">{bot.pair}</div>
          <div className="text-sm text-gray-600 font-medium">{bot.name}</div>
        </div>
        <div className="flex items-center space-x-2">
          <span className="text-2xl">{getTemperatureIcon()}</span>
          <span className={`text-xs px-2 py-1 rounded-full font-bold ${
            bot.status === 'RUNNING' ? 'bg-green-200 text-green-800' : 'bg-gray-200 text-gray-600'
          }`}>
            {bot.status}
          </span>
        </div>
      </div>

      {/* Enhanced Action & Score */}
      <div className="mb-3">
        <div className={`inline-block px-3 py-1 rounded-md text-sm font-bold border ${getActionBadge()}`}>
          {getActionText()}
        </div>
        <div className="text-sm text-gray-700 mt-1">
          Signal: <span className="font-mono font-bold">{bot.current_combined_score.toFixed(3)}</span>
        </div>
      </div>

      {/* Enhanced Signal Strength Bar */}
      <div className="mb-3">
        <div className="flex items-center justify-between text-xs text-gray-600 mb-1">
          <span className="font-medium">Signal Strength</span>
          <span className="font-bold">{(Math.abs(bot.current_combined_score) * 100).toFixed(1)}%</span>
        </div>
        <div className="w-full bg-gray-200 rounded-full h-2">
          <div 
            className={`h-2 rounded-full transition-all duration-300 ${
              bot.current_combined_score < 0 ? 'bg-gradient-to-r from-green-400 to-green-500' :   // Fixed: Negative = BUY (green)
              'bg-gradient-to-r from-red-400 to-red-500'                                       // Fixed: Positive = SELL (red)
            }`}
            style={{ width: `${Math.min(Math.abs(bot.current_combined_score) * 100, 100)}%` }}
          ></div>
        </div>
      </div>

      {/* Enhanced Bottom Stats */}
      <div className="grid grid-cols-2 gap-3 text-sm">
        <div className="bg-white bg-opacity-60 rounded-lg p-2 text-center">
          <div className="text-gray-600 font-medium">Temperature</div>
          <div className="font-bold text-gray-900">{bot.temperature}</div>
        </div>
        <div className="bg-white bg-opacity-60 rounded-lg p-2 text-center">
          <div className="text-gray-600 font-medium">Distance</div>
          <div className="font-bold text-gray-900">
            {bot.distance_to_signal?.toFixed(2) || '--'}
          </div>
        </div>
      </div>
    </div>
  );
};

/**
 * Enhanced Grid Section for Phase 2.4 - Professional bot overview with filtering
 * Designed for full-width (4-column) grid area with responsive layout
 */
const BotGridSection: React.FC<BotGridSectionProps> = ({ 
  className = '' 
}) => {
  const { data: botsData, isLoading, dataUpdatedAt } = useEnhancedBotsStatus();
  const [basicFilter, setBasicFilter] = useState<'ALL' | 'HOT' | 'WARM' | 'COOL' | 'FROZEN' | 'RUNNING'>('ALL');
  const [advancedFilters, setAdvancedFilters] = useState<FilterCriteria>(defaultFilters);
  const [showAdvancedFilters, setShowAdvancedFilters] = useState(false);
  
  // Apply basic filter to advanced filters when basic filter changes
  const handleBasicFilterChange = (filter: typeof basicFilter) => {
    setBasicFilter(filter);
    
    // Update advanced filters to match basic filter
    const updatedFilters = { ...advancedFilters };
    
    // Clear previous filters
    updatedFilters.temperature = [];
    updatedFilters.status = [];
    
    // Set new filters based on basic filter
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
        // ALL - no filters
        break;
    }
    
    setAdvancedFilters(updatedFilters);
  };

  const filteredBots = useFilteredBots(botsData || [], advancedFilters);
  const activeFilterCount = countActiveFilters(advancedFilters);

  // Sort bots by temperature priority, then by signal strength
  const sortedBots = filteredBots.sort((a, b) => {
    const tempPriority = { 'HOT': 4, 'WARM': 3, 'COOL': 2, 'FROZEN': 1 };
    const aPriority = tempPriority[a.temperature as keyof typeof tempPriority] || 0;
    const bPriority = tempPriority[b.temperature as keyof typeof tempPriority] || 0;
    
    if (aPriority !== bPriority) {
      return bPriority - aPriority; // Higher priority first
    }
    
    // Same temperature, sort by signal strength
    return Math.abs(b.current_combined_score) - Math.abs(a.current_combined_score);
  });

  const handleClearFilters = () => {
    setAdvancedFilters(defaultFilters);
    setBasicFilter('ALL');
  };

  // Enhanced loading state
  if (isLoading) {
    return (
      <div className={`bg-white rounded-xl shadow-xl border-2 border-gray-200 p-8 ${className}`}>
        <div className="animate-pulse">
          <div className="h-8 bg-gray-200 rounded w-1/4 mb-6"></div>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6">
            {[1, 2, 3, 4, 5, 6, 7, 8].map((i) => (
              <div key={i} className="h-[200px] bg-gray-200 rounded-xl"></div>
            ))}
          </div>
        </div>
      </div>
    );
  }

  // Count bots by category for enhanced filtering
  const botCounts = {
    total: botsData?.length || 0,
    running: botsData?.filter(bot => bot.status === 'ACTIVE').length || 0,
    hot: botsData?.filter(bot => bot.temperature === 'HOT').length || 0,
    warm: botsData?.filter(bot => bot.temperature === 'WARM').length || 0,
    cool: botsData?.filter(bot => bot.temperature === 'COOL').length || 0,
    frozen: botsData?.filter(bot => bot.temperature === 'FROZEN').length || 0,
  };

  return (
    <div className={`bg-white rounded-xl shadow-xl border-2 border-gray-200 ${className}`}>
      {/* Enhanced Header */}
      <div className="p-8 border-b border-gray-200 bg-gradient-to-r from-blue-50 to-indigo-50">
        <div className="flex items-center justify-between mb-6">
          <div className="flex items-center space-x-4">
            <h2 className="text-3xl font-bold text-gray-900">All Trading Bots</h2>
            <span className="bg-blue-200 text-blue-800 px-4 py-2 rounded-full text-lg font-bold">
              {sortedBots.length} of {botCounts.total}
            </span>
            {activeFilterCount > 0 && (
              <span className="bg-green-200 text-green-800 px-3 py-1 rounded-full text-sm font-bold">
                {activeFilterCount} filter{activeFilterCount !== 1 ? 's' : ''} active
              </span>
            )}
          </div>
          <DataFreshnessIndicator 
            lastUpdated={new Date(dataUpdatedAt || Date.now())}
            size="sm"
            freshThresholdSeconds={10}
            staleThresholdSeconds={20}
          />
        </div>

        {/* Enhanced Filter Controls */}
        <div className="space-y-4">
          {/* Basic Filter Buttons with Counts */}
          <div className="flex flex-wrap gap-3">
            {[
              { key: 'ALL', label: 'All Bots', count: botCounts.total, icon: '🤖' },
              { key: 'RUNNING', label: 'Running', count: botCounts.running, icon: '▶️' },
              { key: 'HOT', label: 'Hot', count: botCounts.hot, icon: '🔥' },
              { key: 'WARM', label: 'Warm', count: botCounts.warm, icon: '🌡️' },
              { key: 'COOL', label: 'Cool', count: botCounts.cool, icon: '❄️' },
              { key: 'FROZEN', label: 'Frozen', count: botCounts.frozen, icon: '🧊' },
            ].map((filterOption) => (
              <button
                key={filterOption.key}
                onClick={() => handleBasicFilterChange(filterOption.key as typeof basicFilter)}
                className={`px-4 py-2 rounded-lg text-sm font-bold transition-all transform hover:scale-105 ${
                  basicFilter === filterOption.key
                    ? 'bg-blue-600 text-white shadow-lg'
                    : 'bg-white text-gray-700 hover:bg-gray-50 border border-gray-300'
                }`}
              >
                <span className="mr-2">{filterOption.icon}</span>
                {filterOption.label}
                <span className="ml-2 bg-black bg-opacity-10 px-2 py-1 rounded-full text-xs">
                  {filterOption.count}
                </span>
              </button>
            ))}
          </div>

          {/* Advanced Filters Toggle */}
          <div className="flex items-center gap-3">
            <AdvancedFilterPanel
              isOpen={showAdvancedFilters}
              onToggle={() => setShowAdvancedFilters(!showAdvancedFilters)}
              filters={advancedFilters}
              onFiltersChange={setAdvancedFilters}
              onClearFilters={handleClearFilters}
              activeFilterCount={activeFilterCount}
            />
            
            {activeFilterCount > 0 && (
              <button
                onClick={handleClearFilters}
                className="px-3 py-1 text-sm text-red-600 hover:text-red-800 underline font-medium"
              >
                Clear All Filters
              </button>
            )}
          </div>
        </div>
      </div>

      {/* Enhanced Bot Grid */}
      <div className="p-8">
        {sortedBots.length === 0 ? (
          <div className="text-center py-12 text-gray-500">
            <div className="text-6xl mb-4">🔍</div>
            <p className="text-xl font-medium">No bots match current filters</p>
            <p className="text-gray-400">Try adjusting your filter criteria</p>
            {activeFilterCount > 0 && (
              <button
                onClick={handleClearFilters}
                className="mt-4 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
              >
                Clear Filters
              </button>
            )}
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 2xl:grid-cols-5 gap-6">
            {sortedBots.map((bot) => (
              <CompactBotCard key={bot.id} bot={bot} />
            ))}
          </div>
        )}
      </div>
    </div>
  );
};

// Export as default
export default BotGridSection;
