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

// Hook for basic trade statistics - UPDATED to use clean data
export const useTradeStats = () => {
  return useQuery<TradeStats>({
    queryKey: ['trades', 'stats-clean'],
    queryFn: async () => {
      const response = await fetch('/api/v1/raw-trades/stats');
      if (!response.ok) {
        throw new Error('Failed to fetch clean trade statistics');
      }
      const data = await response.json();
      
      // Map clean data to expected interface
      return {
        total_trades: data.total_trades,
        filled_trades: data.total_trades, // All raw trades are filled by definition
        success_rate: 100, // All raw trades represent successful executions
        total_volume_usd: data.total_volume_usd
      };
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

// Hook for recent trades - UPDATED to use clean raw trades
export const useRecentTrades = (limit: number = 10) => {
  return useQuery({
    queryKey: ['trades', 'recent-clean', limit],
    queryFn: async () => {
      const response = await fetch(`/api/v1/raw-trades/?limit=${limit}`);
      if (!response.ok) {
        throw new Error('Failed to fetch recent clean trades');
      }
      return response.json();
    },
    refetchInterval: 15000, // Refresh every 15 seconds
    staleTime: 5000, // Consider data stale after 5 seconds
  });
};

// Comprehensive profitability hook - UPDATED to use clean data
export const useProfitabilityData = () => {
  return useQuery<ProfitabilityData>({
    queryKey: ['trades', 'profitability-clean'],
    queryFn: async () => {
      // Get clean stats and P&L data
      const [statsResponse, pnlResponse] = await Promise.all([
        fetch('/api/v1/raw-trades/stats'),
        fetch('/api/v1/raw-trades/pnl-by-product')
      ]);
      
      if (!statsResponse.ok || !pnlResponse.ok) {
        throw new Error('Failed to fetch clean profitability data');
      }
      
      const stats = await statsResponse.json();
      // Note: pnlData available if needed for future enhancements
      
      // Map to expected interface
      return {
        total_trades: stats.total_trades,
        total_volume_usd: stats.total_volume_usd,
        net_pnl: stats.net_pnl,
        success_rate: 100, // All raw trades are successful by definition
        roi_percentage: stats.total_volume_usd > 0 ? (stats.net_pnl / stats.total_volume_usd) * 100 : 0,
        current_balance_usd: 0, // This would need to come from market/accounts
        active_positions_value: 0, // This would need to be calculated separately
        recent_trades: [] // Would come from raw-trades endpoint if needed
      };
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
