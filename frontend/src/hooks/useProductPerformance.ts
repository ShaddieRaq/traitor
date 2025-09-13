import { useQuery } from '@tanstack/react-query';

// Updated interface to match clean raw_trades API
export interface ProductPerformance {
  product_id: string;
  trade_count: number;
  buy_trades: number;
  sell_trades: number;
  total_spent_usd: number;
  total_received_usd: number;
  total_fees_usd: number;
  net_pnl_usd: number;
}

export interface ProductPerformanceResponse {
  products: ProductPerformance[];
}

// UPDATED: Now uses clean raw_trades API instead of corrupted trades API
export const useProductPerformance = () => {
  return useQuery<ProductPerformanceResponse>({
    queryKey: ['product-performance-clean'],
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

export const useBotPerformance = (productId: string) => {
  const { data: performanceData, isLoading, error } = useProductPerformance();
  
  const botPerformance = performanceData?.products.find(
    (p: ProductPerformance) => p.product_id === productId
  );

  return {
    performance: botPerformance,
    isLoading,
    error,
    hasData: !!botPerformance
  };
};
