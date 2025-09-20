import React, { useState, useEffect } from 'react';
import { Search, Settings, X } from 'lucide-react';

export interface FilterCriteria {
  search: string;
  temperature: string[];
  status: string[];
  performanceRange: {
    min: number | null;
    max: number | null;
  };
  signalStrength: {
    min: number | null;
    max: number | null;
  };
  activityLevel: string[];
  sortBy: string;
  sortOrder: 'asc' | 'desc';
}

export interface AdvancedFilterPanelProps {
  isOpen: boolean;
  onToggle: () => void;
  filters: FilterCriteria;
  onFiltersChange: (filters: FilterCriteria) => void;
  onClearFilters: () => void;
  activeFilterCount: number;
}

const temperatureOptions = [
  { value: 'HOT', label: '🔥 HOT', color: 'text-red-600' },
  { value: 'WARM', label: '🌡️ WARM', color: 'text-orange-500' },
  { value: 'COOL', label: '❄️ COOL', color: 'text-blue-500' },
  { value: 'FROZEN', label: '🧊 FROZEN', color: 'text-gray-500' }
];

const statusOptions = [
  { value: 'ACTIVE', label: 'Active', color: 'text-green-600' },
  { value: 'PAUSED', label: 'Paused', color: 'text-yellow-600' },
  { value: 'STOPPED', label: 'Stopped', color: 'text-red-600' }
];

const sortOptions = [
  { value: 'combined_score', label: 'Signal Strength' },
  { value: 'name', label: 'Bot Name' },
  { value: 'status', label: 'Status' },
  { value: 'balance', label: 'Balance' },
  { value: 'last_signal_time', label: 'Last Activity' }
];

export const AdvancedFilterPanel: React.FC<AdvancedFilterPanelProps> = ({
  isOpen,
  onToggle,
  filters,
  onFiltersChange,
  onClearFilters,
  activeFilterCount
}) => {
  const [localFilters, setLocalFilters] = useState<FilterCriteria>(filters);

  // Sync local filters when parent filters change
  useEffect(() => {
    setLocalFilters(filters);
  }, [filters]);

  const handleLocalChange = (newFilters: Partial<FilterCriteria>) => {
    const updated = { ...localFilters, ...newFilters };
    setLocalFilters(updated);
    onFiltersChange(updated);
  };

  const handleArrayToggle = (key: keyof FilterCriteria, value: string) => {
    const currentArray = localFilters[key] as string[];
    const newArray = currentArray.includes(value)
      ? currentArray.filter(item => item !== value)
      : [...currentArray, value];
    
    handleLocalChange({ [key]: newArray });
  };

  const handleRangeChange = (
    rangeKey: 'performanceRange' | 'signalStrength',
    boundKey: 'min' | 'max',
    value: string
  ) => {
    const numValue = value === '' ? null : parseFloat(value);
    handleLocalChange({
      [rangeKey]: {
        ...localFilters[rangeKey],
        [boundKey]: numValue
      }
    });
  };

  const isFilterActive = activeFilterCount > 0;

  return (
    <div className="relative">
      {/* Filter Toggle Button */}
      <button
        onClick={onToggle}
        className={`flex items-center gap-2 px-4 py-2 rounded-lg border transition-colors ${
          isFilterActive
            ? 'bg-blue-50 border-blue-300 text-blue-700'
            : 'bg-white border-gray-300 text-gray-600 hover:bg-gray-50'
        }`}
      >
        <Settings className="h-5 w-5" />
        <span>Advanced Filters</span>
        {isFilterActive && (
          <span className="bg-blue-600 text-white text-xs rounded-full px-2 py-1 min-w-[20px] text-center">
            {activeFilterCount}
          </span>
        )}
      </button>

      {/* Filter Panel */}
      {isOpen && (
        <div className="absolute top-full left-0 mt-2 w-96 bg-white rounded-lg shadow-xl border border-gray-200 p-6 z-50">
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-lg font-semibold text-gray-900">Advanced Filters</h3>
            <div className="flex items-center gap-2">
              {isFilterActive && (
                <button
                  onClick={onClearFilters}
                  className="text-sm text-gray-500 hover:text-gray-700"
                >
                  Clear All
                </button>
              )}
              <button
                onClick={onToggle}
                className="text-gray-400 hover:text-gray-600"
              >
                <X className="h-5 w-5" />
              </button>
            </div>
          </div>

          <div className="space-y-6">
            {/* Search */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Search Bots
              </label>
              <div className="relative">
                <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-gray-400" />
                <input
                  type="text"
                  value={localFilters.search}
                  onChange={(e) => handleLocalChange({ search: e.target.value })}
                  placeholder="Search by name or pair..."
                  className="w-full pl-10 pr-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                />
              </div>
            </div>

            {/* Temperature Filter */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Temperature
              </label>
              <div className="flex flex-wrap gap-2">
                {temperatureOptions.map(option => (
                  <button
                    key={option.value}
                    onClick={() => handleArrayToggle('temperature', option.value)}
                    className={`px-3 py-1 rounded-full text-sm border transition-colors ${
                      localFilters.temperature.includes(option.value)
                        ? 'bg-blue-100 border-blue-300 text-blue-700'
                        : 'bg-white border-gray-300 text-gray-600 hover:bg-gray-50'
                    }`}
                  >
                    {option.label}
                  </button>
                ))}
              </div>
            </div>

            {/* Status Filter */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Status
              </label>
              <div className="flex flex-wrap gap-2">
                {statusOptions.map(option => (
                  <button
                    key={option.value}
                    onClick={() => handleArrayToggle('status', option.value)}
                    className={`px-3 py-1 rounded-full text-sm border transition-colors ${
                      localFilters.status.includes(option.value)
                        ? 'bg-blue-100 border-blue-300 text-blue-700'
                        : 'bg-white border-gray-300 text-gray-600 hover:bg-gray-50'
                    }`}
                  >
                    {option.label}
                  </button>
                ))}
              </div>
            </div>

            {/* Signal Strength Range */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Signal Strength Range
              </label>
              <div className="flex items-center gap-3">
                <input
                  type="number"
                  value={localFilters.signalStrength.min ?? ''}
                  onChange={(e) => handleRangeChange('signalStrength', 'min', e.target.value)}
                  placeholder="Min"
                  step="0.01"
                  min="-1"
                  max="1"
                  className="flex-1 px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                />
                <span className="text-gray-500">to</span>
                <input
                  type="number"
                  value={localFilters.signalStrength.max ?? ''}
                  onChange={(e) => handleRangeChange('signalStrength', 'max', e.target.value)}
                  placeholder="Max"
                  step="0.01"
                  min="-1"
                  max="1"
                  className="flex-1 px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                />
              </div>
              <p className="text-xs text-gray-500 mt-1">Range: -1.0 (strong sell) to +1.0 (strong buy)</p>
            </div>

            {/* Performance Range */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Performance Range (%)
              </label>
              <div className="flex items-center gap-3">
                <input
                  type="number"
                  value={localFilters.performanceRange.min ?? ''}
                  onChange={(e) => handleRangeChange('performanceRange', 'min', e.target.value)}
                  placeholder="Min %"
                  step="0.1"
                  className="flex-1 px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                />
                <span className="text-gray-500">to</span>
                <input
                  type="number"
                  value={localFilters.performanceRange.max ?? ''}
                  onChange={(e) => handleRangeChange('performanceRange', 'max', e.target.value)}
                  placeholder="Max %"
                  step="0.1"
                  className="flex-1 px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                />
              </div>
            </div>

            {/* Sort Options */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Sort By
              </label>
              <div className="flex gap-3">
                <select
                  value={localFilters.sortBy}
                  onChange={(e) => handleLocalChange({ sortBy: e.target.value })}
                  className="flex-1 px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                >
                  {sortOptions.map(option => (
                    <option key={option.value} value={option.value}>
                      {option.label}
                    </option>
                  ))}
                </select>
                <select
                  value={localFilters.sortOrder}
                  onChange={(e) => handleLocalChange({ sortOrder: e.target.value as 'asc' | 'desc' })}
                  className="px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                >
                  <option value="desc">Descending</option>
                  <option value="asc">Ascending</option>
                </select>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default AdvancedFilterPanel;
