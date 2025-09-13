import { useQuery } from '@tanstack/react-query';

export interface BotPerformance {
  bot_id: number;
  bot_name: string;
  pair: string;
  trade_count: number;
  total_spent: number;
  total_received: number;
  realized_pnl: number;
  unrealized_pnl: number;
  total_pnl: number;
  roi_percentage: number;
  current_position: number;
  average_entry_price: number;
  current_price: number;
  total_fees: number;
  buy_count: number;
  sell_count: number;
  first_trade?: string;
  last_trade?: string;
}

// Hook to get bot performance data from the correct API endpoint
export const useBotPerformance = (botId: number) => {
  return useQuery<BotPerformance>({
    queryKey: ['bot-performance', botId],
    queryFn: async () => {
      const response = await fetch(`/api/v1/trades/bot/${botId}/performance`);
      if (!response.ok) {
        throw new Error('Failed to fetch bot performance data');
      }
      return response.json();
    },
    refetchInterval: 15000, // Refresh every 15 seconds for real-time data
    refetchIntervalInBackground: true,
    staleTime: 5000, // Consider data stale after 5 seconds for trading data
    enabled: !!botId, // Only run if botId is provided
  });
};

// Hook to get bot performance by trading pair (needs to map pair to bot ID)
export const useBotPerformanceByPair = (pair: string) => {
  // First get the enhanced bots status to find bot ID for this pair
  const { data: bots } = useQuery({
    queryKey: ['bots', 'enhanced-status'],
    queryFn: async () => {
      const response = await fetch('/api/v1/bots/status/enhanced');
      if (!response.ok) {
        throw new Error('Failed to fetch bots status');
      }
      return response.json();
    },
    refetchInterval: 5000,
    refetchIntervalInBackground: true,
    staleTime: 0,
  });

  // Find the bot ID for this pair
  const bot = bots?.find((b: any) => b.pair === pair);
  const botId = bot?.id;

  return useBotPerformance(botId);
};
