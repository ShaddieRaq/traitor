import { useQuery } from '@tanstack/react-query';
import api from '../lib/api';

interface CacheStats {
  cache_hit_rate: number;
  status: string;
  error?: string;
}

interface CacheStatsResponse {
  cache_performance: CacheStats;
  service_info: {
    service: string;
    status: string;
  };
}

export const useCacheStats = () => {
  return useQuery<CacheStatsResponse>({
    queryKey: ['cache', 'stats'],
    queryFn: async () => {
      const response = await api.get('/cache-monitoring/cache/stats');
      return response.data as CacheStatsResponse;
    },
    refetchInterval: 5000,
    refetchIntervalInBackground: true,
    staleTime: 0
  });
};
