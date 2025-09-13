import { useQuery } from '@tanstack/react-query';

// Updated interface to match clean raw_trades data
export interface Trade {
  id: number;
  fill_id: string;
  order_id: string;
  product_id: string;
  side: string;
  size: number;
  size_in_quote: boolean;
  price: number;
  commission: number;
  created_at: string;
  synced_at: string;
  usd_value: number;
}

// UPDATED: Now fetches from clean raw_trades API
const fetchTrades = async (limit: number = 20): Promise<Trade[]> => {
  const response = await fetch(`/api/v1/raw-trades/?limit=${limit}`);
  if (!response.ok) {
    throw new Error('Failed to fetch clean trades');
  }
  return response.json();
};

export const useTrades = (limit: number = 20) => {
  return useQuery({
    queryKey: ['trades-clean', limit],
    queryFn: () => fetchTrades(limit),
    refetchInterval: 10000, // Fetch every 10 seconds
    refetchIntervalInBackground: true,
    refetchOnWindowFocus: true,
    staleTime: 5000, // Consider data stale after 5 seconds
  });
};
