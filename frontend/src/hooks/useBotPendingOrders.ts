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

// Enhanced interface for new API response
export interface BotPendingOrderDetails {
  bot_id: number;
  bot_name: string;
  bot_pair: string;
  has_pending_orders: boolean;
  pending_order_count: number;
  pending_orders: {
    trade_id: number;
    order_id: string;
    side: string;
    size: number;
    size_usd: number;
    price: number;
    created_at: string;
    time_elapsed_minutes: number;
    time_elapsed_seconds: number;
    urgency: 'fresh' | 'normal' | 'warning' | 'critical';
    product_id: string;
  }[];
  most_recent_pending?: any;
  critical_count: number;
  warning_count: number;
  oldest_pending_minutes: number;
  generated_at: string;
}

const fetchBotPendingOrders = async (botId: number): Promise<BotPendingOrderStatus> => {
  try {
    const response = await fetch(`/api/v1/trades/pending/${botId}`);
    
    if (!response.ok) {
      if (response.status === 404) {
        // Bot not found - return empty status
        return {
          botId,
          hasPendingOrder: false,
          pendingOrderCount: 0,
          mostRecentPendingOrder: undefined
        };
      }
      throw new Error(`Failed to fetch pending orders: ${response.statusText}`);
    }
    
    const data: BotPendingOrderDetails = await response.json();
    
    // Convert new API response to legacy interface for backward compatibility
    return {
      botId,
      hasPendingOrder: data.has_pending_orders,
      pendingOrderCount: data.pending_order_count,
      mostRecentPendingOrder: data.most_recent_pending ? {
        trade_id: data.most_recent_pending.trade_id,
        order_id: data.most_recent_pending.order_id,
        side: data.most_recent_pending.side,
        created_at: data.most_recent_pending.created_at,
        status: 'pending'
      } : undefined
    };
  } catch (error) {
    console.error(`Error fetching pending orders for bot ${botId}:`, error);
    // Return safe default on error
    return {
      botId,
      hasPendingOrder: false,
      pendingOrderCount: 0,
      mostRecentPendingOrder: undefined
    };
  }
};

export const useBotPendingOrders = (botId: number) => {
  return useQuery({
    queryKey: ['bot-pending-orders', botId],
    queryFn: () => fetchBotPendingOrders(botId),
    refetchInterval: 5000, // Check every 5 seconds for real-time updates
    enabled: !!botId, // Only run if botId is provided
    staleTime: 2000, // Consider data stale after 2 seconds
  });
};

// Enhanced hook for detailed pending order information
export const useBotPendingOrderDetails = (botId: number) => {
  return useQuery<BotPendingOrderDetails>({
    queryKey: ['bot-pending-order-details', botId],
    queryFn: async () => {
      const response = await fetch(`/api/v1/trades/pending/${botId}`);
      if (!response.ok) {
        throw new Error(`Failed to fetch pending order details: ${response.statusText}`);
      }
      return response.json();
    },
    refetchInterval: 5000,
    enabled: !!botId,
    staleTime: 2000,
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
    enabled: botIds.length > 0,
    staleTime: 2000,
  });
};

// System-wide pending orders hook for monitoring
export const useSystemPendingOrders = () => {
  return useQuery({
    queryKey: ['system-pending-orders'],
    queryFn: async () => {
      const response = await fetch('/api/v1/trades/pending');
      if (!response.ok) {
        throw new Error(`Failed to fetch system pending orders: ${response.statusText}`);
      }
      return response.json();
    },
    refetchInterval: 10000, // Check every 10 seconds for system overview
    staleTime: 5000,
  });
};
