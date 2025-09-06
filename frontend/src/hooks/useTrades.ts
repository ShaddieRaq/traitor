import { useQuery } from '@tanstack/react-query';

export interface Trade {
  id: number;
  bot_id: number;
  product_id: string;
  side: string;
  size: number;
  price: number;
  fee?: number;
  order_id?: string;
  status: string;
  combined_signal_score?: number;
  created_at: string;
  filled_at?: string;
  // Enhanced fields for information feedback
  action?: string;  // BUY/SELL
  amount?: number;  // USD value
}

const fetchTrades = async (limit: number = 20): Promise<Trade[]> => {
  const response = await fetch(`/api/v1/trades/?limit=${limit}`);
  if (!response.ok) {
    throw new Error('Failed to fetch trades');
  }
  return response.json();
};

export const useTrades = (limit: number = 20) => {
  return useQuery({
    queryKey: ['trades', limit],
    queryFn: () => fetchTrades(limit),
    refetchInterval: 10000, // Fetch every 10 seconds
    refetchIntervalInBackground: true,
    refetchOnWindowFocus: true,
    staleTime: 5000, // Consider data stale after 5 seconds
  });
};
