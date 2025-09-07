import { useQuery } from '@tanstack/react-query';

export interface BotPendingOrderStatus {
  botId: number;
  hasPendingOrder: boolean;
  pendingOrderCount: number;
  mostRecentPendingOrder?: {
    trade_id: number;
    order_id?: string;
    side: string;
    created_at: string;
    status: string;
  };
}

const fetchBotPendingOrders = async (botId: number): Promise<BotPendingOrderStatus> => {
  // Get recent trades for this bot
  const response = await fetch(`/api/v1/trades/recent/${botId}?limit=10`);
  if (!response.ok) {
    throw new Error(`Failed to fetch recent trades for bot ${botId}`);
  }
  
  const trades = await response.json();
  
  // Filter for pending/open orders
  const pendingTrades = trades.filter((trade: any) => 
    trade.status === 'pending' || 
    trade.status === 'open' || 
    trade.status === 'active'
  );
  
  return {
    botId,
    hasPendingOrder: pendingTrades.length > 0,
    pendingOrderCount: pendingTrades.length,
    mostRecentPendingOrder: pendingTrades[0] || undefined
  };
};

export const useBotPendingOrders = (botId: number) => {
  return useQuery({
    queryKey: ['bot-pending-orders', botId],
    queryFn: () => fetchBotPendingOrders(botId),
    refetchInterval: 5000, // Check every 5 seconds
    refetchIntervalInBackground: true,
    refetchOnWindowFocus: true,
    staleTime: 2000, // Consider data stale after 2 seconds
    enabled: !!botId, // Only run if botId is provided
  });
};

// Hook to check all bots for pending orders
export const useAllBotsPendingOrders = (botIds: number[]) => {
  return useQuery({
    queryKey: ['all-bots-pending-orders', botIds],
    queryFn: async () => {
      const results = await Promise.all(
        botIds.map(botId => fetchBotPendingOrders(botId))
      );
      return results;
    },
    refetchInterval: 5000,
    refetchIntervalInBackground: true,
    refetchOnWindowFocus: true,
    staleTime: 2000,
    enabled: botIds.length > 0,
  });
};
