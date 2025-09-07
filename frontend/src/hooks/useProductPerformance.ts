import { useQuery } from '@tanstack/react-query';

export interface ProductPerformance {
  product_id: string;
  trade_count: number;
  total_spent: number;
  total_received: number;
  net_pnl: number;
  roi_percentage: number;
  total_fees: number;
  buy_count: number;
  sell_count: number;
  avg_trade_size: number;
  first_trade: string;
  last_trade: string;
  active_days: number;
  trades_per_day: number;
}

export interface ProductPerformanceResponse {
  products: ProductPerformance[];
  generated_at: string;
  note: string;
}

export const useProductPerformance = () => {
  return useQuery<ProductPerformanceResponse>({
    queryKey: ['product-performance'],
    queryFn: async () => {
      const response = await fetch('/api/v1/trades/performance/by-product');
      if (!response.ok) {
        throw new Error('Failed to fetch product performance');
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
