import { useQuery } from '@tanstack/react-query';
import api from '../lib/api';

interface CacheStats {
  cache_size: number;
  max_cache_size: number;
  cache_ttl_seconds: number;
  total_requests: number;
  hits: number;
  misses: number;
  hit_rate_percent: number;
  evictions: number;
  api_calls_saved: number;
}

interface CacheStatsResponse {
  status: string;
  cache_stats: CacheStats;
  performance_analysis: {
    api_calls_saved: number;
    efficiency_gain: string;
    memory_usage: string;
    cache_health: string;
  };
}

export const useCacheStats = () => {
  return useQuery<CacheStatsResponse>({
    queryKey: ['cache', 'stats'],
    queryFn: async () => {
      const response = await api.get('/cache/stats');
      return response.data as CacheStatsResponse;
    },
    refetchInterval: 5000,
    refetchIntervalInBackground: true,
    staleTime: 0
  });
};
