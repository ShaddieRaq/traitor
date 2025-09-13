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

// NOTE: This hook is deprecated in the clean system since we don't track bot-specific trades
// Raw trades don't have bot_id associations and represent only completed/filled orders
const fetchBotPendingOrders = async (botId: number): Promise<BotPendingOrderStatus> => {
  // In the clean system, all raw_trades are completed by definition
  // Pending orders would need to be tracked separately if needed
  console.warn('useBotPendingOrders is deprecated in clean system - raw trades are always completed');
  
  return {
    botId,
    hasPendingOrder: false,
    pendingOrderCount: 0,
    mostRecentPendingOrder: undefined
  };
};

export const useBotPendingOrders = (botId: number) => {
  return useQuery({
    queryKey: ['bot-pending-orders-deprecated', botId],
    queryFn: () => fetchBotPendingOrders(botId),
    refetchInterval: 30000, // Reduced frequency since it's deprecated
    enabled: !!botId, // Only run if botId is provided
  });
};

// Hook to check all bots for pending orders - DEPRECATED
export const useAllBotsPendingOrders = (botIds: number[]) => {
  return useQuery({
    queryKey: ['all-bots-pending-orders-deprecated', botIds],
    queryFn: async () => {
      const results = await Promise.all(
        botIds.map(botId => fetchBotPendingOrders(botId))
      );
      return results;
    },
    refetchInterval: 30000,
    enabled: botIds.length > 0,
  });
};
