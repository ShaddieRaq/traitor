import React, { useState } from 'react';
import { useEnhancedBotsStatus } from '../../hooks/useBots';
import { useFilteredBots, countActiveFilters, defaultFilters } from '../../hooks/useFilteredBots';
import AdvancedFilterPanel, { FilterCriteria } from './AdvancedFilterPanel';
import MiniChart from './MiniChart';
import { DataFreshnessIndicator } from '../DataFreshnessIndicators';

interface BotGridSectionProps {
  className?: string;
}

interface CompactBotCardProps {
  bot: any;
}

/**
 * Compact bot card for grid display
 */
const CompactBotCard: React.FC<CompactBotCardProps> = ({ bot }) => {
  const getTemperatureColor = () => {
    switch (bot.temperature) {
      case 'HOT': return 'border-red-200 bg-red-50';
      case 'WARM': return 'border-orange-200 bg-orange-50';
      case 'COOL': return 'border-blue-200 bg-blue-50';
      default: return 'border-gray-200 bg-gray-50';
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

  const getActionColor = () => {
    if (bot.current_combined_score > 0.1) return 'text-green-600';
    if (bot.current_combined_score < -0.1) return 'text-red-600';
    return 'text-gray-600';
  };

  const getActionText = () => {
    if (bot.current_combined_score > 0.1) return 'BUY';
    if (bot.current_combined_score < -0.1) return 'SELL';
    return 'HOLD';
  };

  // Generate mock signal history for mini chart
  const generateSignalHistory = () => {
    const points = 8;
    const currentScore = bot.current_combined_score || 0;
    return Array.from({ length: points }, (_, i) => {
      const progress = i / (points - 1);
      const trend = currentScore * progress;
      const noise = (Math.random() - 0.5) * 0.2;
      return Math.max(-1, Math.min(1, trend + noise));
    });
  };

  return (
    <div className={`
      ${getTemperatureColor()}
      rounded-lg border-2 p-4 hover:shadow-md transition-shadow
      h-[180px] flex flex-col justify-between
    `}>
      {/* Header */}
      <div className="flex items-center justify-between mb-2">
        <div>
          <div className="font-semibold text-gray-900 text-sm">{bot.pair}</div>
          <div className="text-xs text-gray-600">{bot.name}</div>
        </div>
        <div className="flex items-center space-x-1">
          <span className="text-lg">{getTemperatureIcon()}</span>
          <span className={`text-xs px-1 py-0.5 rounded ${
            bot.status === 'RUNNING' ? 'bg-green-100 text-green-800' : 'bg-gray-100 text-gray-600'
          }`}>
            {bot.status}
          </span>
        </div>
      </div>

      {/* Action & Score */}
      <div className="mb-2">
        <div className={`text-lg font-bold ${getActionColor()}`}>
          {getActionText()}
        </div>
        <div className="text-xs text-gray-600">
          Score: <span className="font-mono">{bot.current_combined_score.toFixed(3)}</span>
        </div>
      </div>

      {/* Mini Signal Chart */}
      <div className="mb-2 h-8">
        <MiniChart
          data={generateSignalHistory()}
          height={32}
          type="line"
          showGrid={false}
          showAxes={false}
          gradient={false}
          color={getActionColor().includes('green') ? '#10B981' : 
                getActionColor().includes('red') ? '#EF4444' : '#6B7280'}
        />
      </div>

      {/* Bottom Stats */}
      <div className="grid grid-cols-2 gap-2 text-xs">
        <div>
          <div className="text-gray-500">Temp</div>
          <div className="font-medium">{bot.temperature}</div>
        </div>
        <div>
          <div className="text-gray-500">Distance</div>
          <div className="font-medium">
            {bot.distance_to_signal?.toFixed(2) || '--'}
          </div>
        </div>
      </div>
    </div>
  );
};

/**
 * Grid section showing all bots in compact card format
 * Designed for full-width grid area with responsive columns
 */
export const BotGridSection: React.FC<BotGridSectionProps> = ({ 
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

  const handleClearFilters = () => {
    setAdvancedFilters(defaultFilters);
    setBasicFilter('ALL');
  };

  if (isLoading) {
    return (
      <div className={`bg-white rounded-lg shadow-lg border p-6 ${className}`}>
        <div className="animate-pulse">
          <div className="h-6 bg-gray-200 rounded w-1/4 mb-4"></div>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4">
            {[1, 2, 3, 4, 5, 6, 7, 8].map((i) => (
              <div key={i} className="h-[160px] bg-gray-200 rounded-lg"></div>
            ))}
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className={`bg-white rounded-lg shadow-lg border p-6 ${className}`}>
      {/* Header with Filters */}
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center space-x-2">
          <h2 className="text-lg font-semibold text-gray-900">All Bots</h2>
          <span className="bg-blue-100 text-blue-800 px-2 py-1 rounded-full text-sm font-medium">
            {filteredBots.length} of {botsData?.length || 0}
          </span>
          {activeFilterCount > 0 && (
            <span className="bg-green-100 text-green-800 px-2 py-1 rounded-full text-xs font-medium">
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

      {/* Filter Controls */}
      <div className="space-y-3 mb-4">
        {/* Basic Filter Buttons */}
        <div className="flex flex-wrap gap-2">
          {(['ALL', 'RUNNING', 'HOT', 'WARM', 'COOL', 'FROZEN'] as const).map((filterOption) => (
            <button
              key={filterOption}
              onClick={() => handleBasicFilterChange(filterOption)}
              className={`px-3 py-1 rounded-full text-xs font-medium transition-colors ${
                basicFilter === filterOption
                  ? 'bg-blue-500 text-white'
                  : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
              }`}
            >
              {filterOption}
              {filterOption !== 'ALL' && (
                <span className="ml-1">
                  ({botsData?.filter(bot => 
                    filterOption === 'RUNNING' 
                      ? bot.status === 'ACTIVE'
                      : bot.temperature === filterOption
                  ).length || 0})
                </span>
              )}
            </button>
          ))}
        </div>

        {/* Advanced Filters */}
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
              className="text-sm text-gray-500 hover:text-gray-700 underline"
            >
              Clear all filters
            </button>
          )}
        </div>
      </div>

      {/* Bots Grid */}
      {filteredBots.length > 0 ? (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4">
          {filteredBots.map((bot) => (
            <CompactBotCard key={`bot-grid-${bot.id}`} bot={bot} />
          ))}
        </div>
      ) : (
        <div className="text-center py-8 text-gray-500">
          <div className="text-4xl mb-2">🔍</div>
          <div className="text-lg font-medium">No Bots Found</div>
          <div className="text-sm">No bots match the current filters</div>
        </div>
      )}

      {/* Summary Stats */}
      <div className="mt-6 pt-4 border-t border-gray-200">
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-center">
          <div>
            <div className="text-sm text-gray-600">Running</div>
            <div className="text-lg font-semibold text-green-600">
              {botsData?.filter(b => b.status === 'RUNNING').length || 0}
            </div>
          </div>
          <div>
            <div className="text-sm text-gray-600">Hot</div>
            <div className="text-lg font-semibold text-red-600">
              {botsData?.filter(b => b.temperature === 'HOT').length || 0}
            </div>
          </div>
          <div>
            <div className="text-sm text-gray-600">Warm</div>
            <div className="text-lg font-semibold text-orange-600">
              {botsData?.filter(b => b.temperature === 'WARM').length || 0}
            </div>
          </div>
          <div>
            <div className="text-sm text-gray-600">Cool/Frozen</div>
            <div className="text-lg font-semibold text-blue-600">
              {botsData?.filter(b => ['COOL', 'FROZEN'].includes(b.temperature)).length || 0}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default BotGridSection;
