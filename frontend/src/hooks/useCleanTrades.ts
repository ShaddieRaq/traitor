import { useQuery } from '@tanstack/react-query';

// Clean data interfaces matching the raw_trades API
export interface CleanProductPerformance {
  product_id: string;
  trade_count: number;
  buy_trades: number;
  sell_trades: number;
  total_spent_usd: number;
  total_received_usd: number;
  total_fees_usd: number;
  net_pnl_usd: number;
}

export interface CleanProductPerformanceResponse {
  products: CleanProductPerformance[];
}

export interface CleanTradingStats {
  total_trades: number;
  total_products: number;
  total_volume_usd: number;
  total_fees: number;
  net_pnl: number;
}

export interface CleanRawTrade {
  id: number;
  fill_id: string;
  order_id: string;
  product_id: string;
  side: string;
  size: number;
  size_in_quote: boolean;
  price: number;
  commission: number;
  created_at: string;
  synced_at: string;
  usd_value: number;
}

// Hook for clean product performance data (replaces corrupted useProductPerformance)
export const useCleanProductPerformance = () => {
  return useQuery<CleanProductPerformanceResponse>({
    queryKey: ['clean-product-performance'],
    queryFn: async () => {
      const response = await fetch('/api/v1/raw-trades/pnl-by-product');
      if (!response.ok) {
        throw new Error('Failed to fetch clean product performance');
      }
      return response.json();
    },
    refetchInterval: 30000, // Refresh every 30 seconds
    refetchIntervalInBackground: true,
    staleTime: 15000, // Consider data stale after 15 seconds
  });
};

// Hook for clean trading statistics (replaces corrupted useTradeStats)
export const useCleanTradingStats = () => {
  return useQuery<CleanTradingStats>({
    queryKey: ['clean-trading-stats'],
    queryFn: async () => {
      const response = await fetch('/api/v1/raw-trades/stats');
      if (!response.ok) {
        throw new Error('Failed to fetch clean trading stats');
      }
      return response.json();
    },
    refetchInterval: 30000, // Refresh every 30 seconds
    staleTime: 15000, // Consider data stale after 15 seconds
  });
};

// Hook for clean raw trades (replaces corrupted useRecentTrades)
export const useCleanRawTrades = (productId?: string, limit: number = 100) => {
  return useQuery<CleanRawTrade[]>({
    queryKey: ['clean-raw-trades', productId, limit],
    queryFn: async () => {
      const url = productId 
        ? `/api/v1/raw-trades/?product_id=${productId}&limit=${limit}`
        : `/api/v1/raw-trades/?limit=${limit}`;
      
      const response = await fetch(url);
      if (!response.ok) {
        throw new Error('Failed to fetch clean raw trades');
      }
      return response.json();
    },
    refetchInterval: 15000, // Refresh every 15 seconds
    staleTime: 5000, // Consider data stale after 5 seconds
  });
};

// Hook for specific product performance (replaces corrupted useBotPerformance)
export const useCleanBotPerformance = (productId: string) => {
  const { data: performanceData, isLoading, error } = useCleanProductPerformance();
  
  const botPerformance = performanceData?.products.find(
    (p: CleanProductPerformance) => p.product_id === productId
  );

  return {
    data: botPerformance,
    isLoading,
    error,
  };
};

// Hook for trades by order ID
export const useCleanTradesByOrder = (orderId: string) => {
  return useQuery<CleanRawTrade[]>({
    queryKey: ['clean-trades-by-order', orderId],
    queryFn: async () => {
      const response = await fetch(`/api/v1/raw-trades/by-order/${orderId}`);
      if (!response.ok) {
        if (response.status === 404) {
          return []; // No trades found for this order
        }
        throw new Error('Failed to fetch trades by order');
      }
      return response.json();
    },
    enabled: !!orderId, // Only run if orderId is provided
    staleTime: 60000, // Order data doesn't change frequently
  });
};

// Summary hook that provides comprehensive clean data
export const useCleanProfitabilityData = () => {
  const { data: stats, isLoading: statsLoading, error: statsError } = useCleanTradingStats();
  const { data: performance, isLoading: perfLoading, error: perfError } = useCleanProductPerformance();
  
  return {
    data: {
      total_trades: stats?.total_trades || 0,
      total_products: stats?.total_products || 0,
      total_volume_usd: stats?.total_volume_usd || 0,
      total_fees: stats?.total_fees || 0,
      net_pnl: stats?.net_pnl || 0,
      products: performance?.products || []
    },
    isLoading: statsLoading || perfLoading,
    error: statsError || perfError,
  };
};
