import { useMemo } from 'react';
import { EnhancedBotStatus } from '../types';
import { FilterCriteria } from '../components/Dashboard/AdvancedFilterPanel';

export const useFilteredBots = (bots: EnhancedBotStatus[], filters: FilterCriteria) => {
  return useMemo(() => {
    if (!bots || bots.length === 0) return [];

    let filtered = bots.filter(bot => {
      // Search filter
      if (filters.search) {
        const searchTerm = filters.search.toLowerCase();
        const botName = bot.name?.toLowerCase() || '';
        const productPair = bot.pair?.toLowerCase() || '';
        if (!botName.includes(searchTerm) && !productPair.includes(searchTerm)) {
          return false;
        }
      }

      // Temperature filter
      if (filters.temperature.length > 0) {
        const botTemp = bot.temperature || 'FROZEN';
        if (!filters.temperature.includes(botTemp)) {
          return false;
        }
      }

      // Status filter
      if (filters.status.length > 0) {
        const botStatus = bot.status || 'STOPPED';
        if (!filters.status.includes(botStatus)) {
          return false;
        }
      }

      // Signal strength range filter
      if (filters.signalStrength.min !== null || filters.signalStrength.max !== null) {
        const signalScore = bot.current_combined_score || 0;
        if (filters.signalStrength.min !== null && signalScore < filters.signalStrength.min) {
          return false;
        }
        if (filters.signalStrength.max !== null && signalScore > filters.signalStrength.max) {
          return false;
        }
      }

      // Performance range filter (if we have P&L data)
      if (filters.performanceRange.min !== null || filters.performanceRange.max !== null) {
        // For now, we'll skip this filter since we don't have direct P&L per bot
        // This can be enhanced when we add individual bot performance data
      }

      return true;
    });

    // Apply sorting
    filtered.sort((a, b) => {
      let aValue: any;
      let bValue: any;

      switch (filters.sortBy) {
        case 'name':
          aValue = a.name || '';
          bValue = b.name || '';
          break;
        case 'status':
          aValue = a.status || '';
          bValue = b.status || '';
          break;
        case 'balance':
          // Use current_position_size as a proxy for balance activity
          aValue = a.current_position_size || 0;
          bValue = b.current_position_size || 0;
          break;
        case 'last_signal_time':
          // For now, use creation order since we don't have last_signal_time
          // This can be enhanced when that field is available
          aValue = a.id || 0;
          bValue = b.id || 0;
          break;
        case 'combined_score':
        default:
          aValue = a.current_combined_score || 0;
          bValue = b.current_combined_score || 0;
          break;
      }

      if (filters.sortOrder === 'asc') {
        return aValue < bValue ? -1 : aValue > bValue ? 1 : 0;
      } else {
        return aValue > bValue ? -1 : aValue < bValue ? 1 : 0;
      }
    });

    return filtered;
  }, [bots, filters]);
};

// Helper function to count active filters
export const countActiveFilters = (filters: FilterCriteria): number => {
  let count = 0;
  
  if (filters.search) count++;
  if (filters.temperature.length > 0) count++;
  if (filters.status.length > 0) count++;
  if (filters.signalStrength.min !== null || filters.signalStrength.max !== null) count++;
  if (filters.performanceRange.min !== null || filters.performanceRange.max !== null) count++;
  
  return count;
};

// Default filter state
export const defaultFilters: FilterCriteria = {
  search: '',
  temperature: [],
  status: [],
  performanceRange: { min: null, max: null },
  signalStrength: { min: null, max: null },
  activityLevel: [],
  sortBy: 'combined_score',
  sortOrder: 'desc'
};
