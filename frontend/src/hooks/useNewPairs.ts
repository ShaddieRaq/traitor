import { useQuery } from '@tanstack/react-query';
import api from '../lib/api';

export interface NewPair {
  product_id: string;
  base_name: string;
  base_currency_id: string;
  status: string;
  trading_disabled: boolean;
  first_seen: string;
  initial_price: number | null;
  initial_volume_24h: number | null;
  is_new_listing: boolean;
  days_since_listing: number;
}

export interface NewPairStats {
  total_pairs_tracked: number;
  usd_pairs_tracked: number;
  unprocessed_new_pairs: number;
  pairs_discovered_last_7_days: number;
  latest_discovery: {
    product_id: string;
    base_name: string;
    discovered_at: string;
  } | null;
}

export interface NewPairScanResult {
  success: boolean;
  timestamp: string;
  total_products_scanned: number;
  existing_pairs_tracked: number;
  new_pairs_found: number;
  usd_pairs_found: number;
  pairs_updated: number;
  new_pairs: Array<{
    product_id: string;
    base_name: string;
    initial_price: number;
    initial_volume: number;
  }>;
}

export const useNewPairStats = () => {
  return useQuery({
    queryKey: ['new-pairs', 'stats'],
    queryFn: async () => {
      const response = await api.get('/new-pairs/stats');
      return response.data;
    },
    refetchInterval: 300000, // Refresh every 5 minutes
    staleTime: 60000, // Consider data stale after 1 minute
  });
};

export const useRecentNewPairs = (days: number = 7) => {
  return useQuery({
    queryKey: ['new-pairs', 'recent', days],
    queryFn: async () => {
      const response = await api.get(`/new-pairs/recent?days=${days}`);
      return response.data;
    },
    refetchInterval: 300000, // Refresh every 5 minutes
    staleTime: 60000, // Consider data stale after 1 minute
  });
};

export const useTriggerNewPairScan = () => {
  return useQuery({
    queryKey: ['new-pairs', 'manual-scan'],
    queryFn: async () => {
      const response = await api.get('/new-pairs/scan');
      return response.data as NewPairScanResult;
    },
    enabled: false, // Only run when manually triggered
  });
};

export const useAnalyzeNewPair = (productId: string) => {
  return useQuery({
    queryKey: ['new-pairs', 'analyze', productId],
    queryFn: async () => {
      const response = await api.get(`/new-pairs/analyze/${productId}`);
      return response.data;
    },
    enabled: !!productId,
    staleTime: 30000, // Consider data stale after 30 seconds
  });
};
