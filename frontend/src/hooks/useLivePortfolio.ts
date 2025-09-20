import { useQuery } from '@tanstack/react-query';

export interface LiveHolding {
  currency: string;
  balance: number;
  price: number;
  value_usd: number;
}

export interface LivePortfolioData {
  total_portfolio_value_usd: number;
  holdings: LiveHolding[];
  last_updated: string;
}

/**
 * Hook for live portfolio data from Coinbase accounts
 * This is the source of truth for current portfolio value and positions
 */
export const useLivePortfolio = () => {
  return useQuery<LivePortfolioData>({
    queryKey: ['live-portfolio'],
    queryFn: async () => {
      const response = await fetch('/api/v1/market/portfolio/live');
      if (!response.ok) {
        throw new Error('Failed to fetch live portfolio data');
      }
      return response.json();
    },
    refetchInterval: 10000, // Update every 10 seconds for live data
    refetchIntervalInBackground: true,
    staleTime: 5000, // Consider data stale after 5 seconds
  });
};
