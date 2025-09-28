import { useQuery } from '@tanstack/react-query';
import api from '../lib/api';

interface SystemStatus {
  status: 'healthy' | 'degraded' | 'error';
  timestamp: string;
  active_errors?: number;  // Add optional field for error count
  services: {
    coinbase_api: {
      status: 'healthy' | 'unhealthy';
      last_activity?: string;
    };
    database: {
      status: 'healthy' | 'unhealthy';
    };
    polling: {
      status: 'active' | 'inactive';
      interval_seconds: number;
    };
  };
  data_freshness: {
    market_data: {
      healthy: boolean;
      last_update?: string;
      seconds_since_update?: number;
    };
  };
  error?: string;
}

export const useSystemStatus = () => {
  return useQuery({
    queryKey: ['system', 'status'],
    queryFn: async () => {
      // Get both system status and error health
      const [systemResponse, healthResponse] = await Promise.all([
        api.get('/market/system/status'),
        api.get('/system-errors/health')
      ]);
      
      const systemStatus = systemResponse.data as SystemStatus;
      const healthData = healthResponse.data;
      
      // Override status if there are active errors
      if (healthData.status === 'issues' && healthData.active_errors > 0) {
        systemStatus.status = 'degraded';
        systemStatus.active_errors = healthData.active_errors;
      }
      
      return systemStatus;
    },
    refetchInterval: 10000, // Check system status every 10 seconds
    refetchIntervalInBackground: true,
    refetchOnWindowFocus: true,
    staleTime: 5000, // Consider data stale after 5 seconds
  });
};

// Helper function to determine overall system health
export const getSystemHealthColor = (status?: SystemStatus) => {
  if (!status) return 'bg-gray-400';
  
  switch (status.status) {
    case 'healthy':
      return 'bg-green-400';
    case 'degraded':
      return 'bg-yellow-400';
    case 'error':
      return 'bg-red-400';
    default:
      return 'bg-gray-400';
  }
};

// Helper function to get service status text
export const getServiceStatusText = (status?: SystemStatus) => {
  if (!status) return 'Unknown';
  
  const { coinbase_api, database, polling } = status.services;
  
  if (coinbase_api.status === 'healthy' && database.status === 'healthy' && polling.status === 'active') {
    return 'All Services Online';
  }
  
  const issues = [];
  if (coinbase_api.status !== 'healthy') issues.push('API');
  if (database.status !== 'healthy') issues.push('Database');
  if (polling.status !== 'active') issues.push('Polling');
  
  return issues.length > 0 ? `Issues: ${issues.join(', ')}` : 'Partial Service';
};
