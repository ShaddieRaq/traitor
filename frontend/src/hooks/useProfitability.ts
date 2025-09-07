import { useQuery } from '@tanstack/react-query';

interface ProfitabilityData {
  total_trades: number;
  total_volume_usd: number;
  net_pnl: number;
  success_rate: number;
  roi_percentage: number;
  daily_pnl?: number;
  weekly_pnl?: number;
  current_balance_usd: number;
  active_positions_value: number;
  recent_trades?: Array<{
    id: number;
    side: string;
    size: number;
    price: number;
    created_at: string;
    pnl?: number;
  }>;
}

interface TradeStats {
  total_trades: number;
  filled_trades: number;
  success_rate: number;
  total_volume_usd?: number;
}

interface AccountBalance {
  currency: string;
  available_balance: number;
  is_cash: boolean;
}

// Hook for basic trade statistics
export const useTradeStats = () => {
  return useQuery<TradeStats>({
    queryKey: ['trades', 'stats'],
    queryFn: async () => {
      const response = await fetch('/api/v1/trades/stats');
      if (!response.ok) {
        throw new Error('Failed to fetch trade statistics');
      }
      return response.json();
    },
    refetchInterval: 30000, // Refresh every 30 seconds
    staleTime: 15000, // Consider data stale after 15 seconds
  });
};

// Hook for account balances
export const useAccountBalances = () => {
  return useQuery<AccountBalance[]>({
    queryKey: ['market', 'accounts'],
    queryFn: async () => {
      const response = await fetch('/api/v1/market/accounts');
      if (!response.ok) {
        throw new Error('Failed to fetch account balances');
      }
      return response.json();
    },
    refetchInterval: 60000, // Refresh every minute
    staleTime: 30000, // Consider data stale after 30 seconds
  });
};

// Hook for recent trades
export const useRecentTrades = (limit: number = 10) => {
  return useQuery({
    queryKey: ['trades', 'recent', limit],
    queryFn: async () => {
      const response = await fetch(`/api/v1/trades/?limit=${limit}`);
      if (!response.ok) {
        throw new Error('Failed to fetch recent trades');
      }
      return response.json();
    },
    refetchInterval: 15000, // Refresh every 15 seconds
    staleTime: 5000, // Consider data stale after 5 seconds
  });
};

// Comprehensive profitability hook that uses the backend profitability endpoint
export const useProfitabilityData = () => {
  return useQuery<ProfitabilityData>({
    queryKey: ['trades', 'profitability'],
    queryFn: async () => {
      const response = await fetch('/api/v1/trades/profitability');
      if (!response.ok) {
        throw new Error('Failed to fetch profitability data');
      }
      return response.json();
    },
    refetchInterval: 30000, // Refresh every 30 seconds
    staleTime: 15000, // Consider data stale after 15 seconds
  });
};

// Hook for live P&L updates (could be enhanced with WebSocket in the future)
export const useLivePnL = () => {
  const { data: profitabilityData, ...rest } = useProfitabilityData();
  
  return {
    data: profitabilityData,
    isProfit: profitabilityData ? profitabilityData.net_pnl > 0 : false,
    isLoss: profitabilityData ? profitabilityData.net_pnl < 0 : false,
    ...rest,
  };
};
