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

// Raw trade product performance interface (from actual current data)
interface RawTradeProductPerformance {
  product_id: string;
  trade_count: number;
  buy_trades: number;
  sell_trades: number;
  total_spent_usd: number;
  total_received_usd: number;
  total_fees_usd: number;
  realized_pnl_usd: number;
  unrealized_pnl_usd: number;
  net_pnl_usd: number;
  current_holdings: number;
  current_value: number;
  current_price?: number;
  average_buy_price?: number;
}

// Hook to get bot performance data from the DEPRECATED Trade table
// WARNING: This endpoint uses stale data from the deprecated Trade model
export const useBotPerformanceDeprecated = (botId: number) => {
  return useQuery<BotPerformance>({
    queryKey: ['bot-performance-deprecated', botId],
    queryFn: async () => {
      const response = await fetch(`/api/v1/trades/bot/${botId}/performance`);
      if (!response.ok) {
        throw new Error('Failed to fetch bot performance data');
      }
      return response.json();
    },
    refetchInterval: 15000,
    refetchIntervalInBackground: true,
    staleTime: 5000,
    enabled: !!botId,
  });
};

// Hook to get current bot performance from raw trades (CURRENT DATA)
export const useBotPerformance = (botId: number) => {
  // Get all raw trade product performance data
  const { data: rawProductData, isLoading: productsLoading } = useQuery({
    queryKey: ['raw-trades', 'pnl-by-product'],
    queryFn: async () => {
      const response = await fetch('/api/v1/raw-trades/pnl-by-product');
      if (!response.ok) {
        throw new Error('Failed to fetch raw trades product performance');
      }
      const data = await response.json();
      return data.products as RawTradeProductPerformance[];
    },
    refetchInterval: 15000,
    refetchIntervalInBackground: true,
    staleTime: 5000,
  });

  // Get bot details to find the trading pair
  const { data: bots, isLoading: botsLoading } = useQuery({
    queryKey: ['bots'],
    queryFn: async () => {
      const response = await fetch('/api/v1/bots/');
      if (!response.ok) {
        throw new Error('Failed to fetch bots');
      }
      return response.json();
    },
    refetchInterval: 15000,
    refetchIntervalInBackground: true,
    staleTime: 5000,
  });

  return useQuery<BotPerformance>({
    queryKey: ['bot-performance-current', botId],
    queryFn: async () => {
      // Find the bot and its trading pair
      const bot = bots?.find((b: any) => b.id === botId);
      if (!bot) {
        throw new Error('Bot not found');
      }

      // Find the performance data for this product
      const productPerformance = rawProductData?.find(p => p.product_id === bot.pair);
      if (!productPerformance) {
        // Return empty performance data if no trades exist
        return {
          bot_id: botId,
          bot_name: bot.name,
          pair: bot.pair,
          trade_count: 0,
          total_spent: 0,
          total_received: 0,
          realized_pnl: 0,
          unrealized_pnl: 0,
          total_pnl: 0,
          roi_percentage: 0,
          current_position: 0,
          average_entry_price: 0,
          current_price: 0,
          total_fees: 0,
          buy_count: 0,
          sell_count: 0,
        };
      }

      // Convert raw trade data to bot performance format
      const roiPercentage = productPerformance.total_spent_usd > 0 
        ? (productPerformance.net_pnl_usd / productPerformance.total_spent_usd) * 100 
        : 0;

      return {
        bot_id: botId,
        bot_name: bot.name,
        pair: bot.pair,
        trade_count: productPerformance.trade_count,
        total_spent: productPerformance.total_spent_usd,
        total_received: productPerformance.total_received_usd,
        realized_pnl: productPerformance.realized_pnl_usd, // Use actual realized P&L
        unrealized_pnl: productPerformance.unrealized_pnl_usd, // Use actual unrealized P&L
        total_pnl: productPerformance.net_pnl_usd, // Total = realized + unrealized
        roi_percentage: roiPercentage,
        current_position: productPerformance.current_holdings, // Use calculated holdings
        average_entry_price: productPerformance.average_buy_price || 0,
        current_price: productPerformance.current_price || 0,
        total_fees: productPerformance.total_fees_usd,
        buy_count: productPerformance.buy_trades,
        sell_count: productPerformance.sell_trades,
      };
    },
    enabled: !!botId && !!bots && !!rawProductData && !botsLoading && !productsLoading,
    refetchInterval: 15000,
    refetchIntervalInBackground: true,
    staleTime: 5000,
  });
};

// Hook to get bot performance by trading pair (uses current raw trades data)
export const useBotPerformanceByPair = (pair: string) => {
  // Get all raw trade product performance data
  const { data: rawProductData, isLoading: productsLoading } = useQuery({
    queryKey: ['raw-trades', 'pnl-by-product'],
    queryFn: async () => {
      const response = await fetch('/api/v1/raw-trades/pnl-by-product');
      if (!response.ok) {
        throw new Error('Failed to fetch raw trades product performance');
      }
      const data = await response.json();
      return data.products as RawTradeProductPerformance[];
    },
    refetchInterval: 15000,
    refetchIntervalInBackground: true,
    staleTime: 5000,
  });

  // Get bot details to find the bot for this pair
  const { data: bots, isLoading: botsLoading } = useQuery({
    queryKey: ['bots'],
    queryFn: async () => {
      const response = await fetch('/api/v1/bots/');
      if (!response.ok) {
        throw new Error('Failed to fetch bots');
      }
      return response.json();
    },
    refetchInterval: 15000,
    refetchIntervalInBackground: true,
    staleTime: 5000,
  });

  return useQuery<BotPerformance>({
    queryKey: ['bot-performance-by-pair', pair],
    queryFn: async () => {
      // Find the bot for this trading pair
      const bot = bots?.find((b: any) => b.pair === pair);
      if (!bot) {
        throw new Error(`No bot found for pair ${pair}`);
      }

      // Find the performance data for this product
      const productPerformance = rawProductData?.find(p => p.product_id === pair);
      if (!productPerformance) {
        // Return empty performance data if no trades exist
        return {
          bot_id: bot.id,
          bot_name: bot.name,
          pair: pair,
          trade_count: 0,
          total_spent: 0,
          total_received: 0,
          realized_pnl: 0,
          unrealized_pnl: 0,
          total_pnl: 0,
          roi_percentage: 0,
          current_position: 0,
          average_entry_price: 0,
          current_price: 0,
          total_fees: 0,
          buy_count: 0,
          sell_count: 0,
        };
      }

      // Convert raw trade data to bot performance format
      const roiPercentage = productPerformance.total_spent_usd > 0 
        ? (productPerformance.net_pnl_usd / productPerformance.total_spent_usd) * 100 
        : 0;

      return {
        bot_id: bot.id,
        bot_name: bot.name,
        pair: pair,
        trade_count: productPerformance.trade_count,
        total_spent: productPerformance.total_spent_usd,
        total_received: productPerformance.total_received_usd,
        realized_pnl: productPerformance.realized_pnl_usd, // FIXED: Use actual realized P&L
        unrealized_pnl: productPerformance.unrealized_pnl_usd, // FIXED: Use actual unrealized P&L
        total_pnl: productPerformance.net_pnl_usd,
        roi_percentage: roiPercentage,
        current_position: productPerformance.current_holdings || 0, // Use calculated holdings
        average_entry_price: productPerformance.average_buy_price || 0, // Use calculated average
        current_price: productPerformance.current_price || 0, // Use current market price
        total_fees: productPerformance.total_fees_usd,
        buy_count: productPerformance.buy_trades,
        sell_count: productPerformance.sell_trades,
      };
    },
    enabled: !!pair && !!bots && !!rawProductData && !botsLoading && !productsLoading,
    refetchInterval: 15000,
    refetchIntervalInBackground: true,
    staleTime: 5000,
  });
};
