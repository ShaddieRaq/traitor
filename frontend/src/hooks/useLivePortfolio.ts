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
      const response = await fetch('/api/v1/market/accounts');
      if (!response.ok) {
        throw new Error('Failed to fetch live portfolio data');
      }
      const accounts = await response.json();
      
      // Calculate portfolio from accounts data
      let totalUSD = 0;
      let usdBalance = 0;
      let cryptoValue = 0;
      const holdings: LiveHolding[] = [];
      
      for (const account of accounts) {
        const balance = account.available_balance || 0;
        if (balance > 0) {
          const currency = account.currency;
          if (currency === 'USD' || currency === 'USDC') {
            usdBalance += balance;
            totalUSD += balance;
            holdings.push({
              currency,
              balance,
              price: 1,
              value_usd: balance
            });
          } else {
            // For crypto, fetch current market price
            try {
              const product_id = `${currency}-USD`;
              const tickerResponse = await fetch(`/api/v1/market/ticker/${product_id}`);
              if (tickerResponse.ok) {
                const ticker = await tickerResponse.json();
                const price = parseFloat(ticker.price || 0);
                const valueUSD = balance * price;
                cryptoValue += valueUSD;
                totalUSD += valueUSD;
                holdings.push({
                  currency,
                  balance,
                  price,
                  value_usd: valueUSD
                });
              } else {
                // Skip assets we can't price
                console.warn(`Could not fetch price for ${currency}, skipping`);
              }
            } catch (e) {
              console.warn(`Error fetching price for ${currency}:`, e);
            }
          }
        }
      }
      
      // Transform to portfolio format
      return {
        total_portfolio_value_usd: totalUSD,
        holdings: [
          {
            currency: 'USD',
            balance: usdBalance,
            price: 1,
            value_usd: usdBalance
          },
          {
            currency: 'CRYPTO',
            balance: cryptoValue,
            price: 1,
            value_usd: cryptoValue
          }
        ],
        last_updated: new Date().toISOString()
      } as LivePortfolioData;
    },
    refetchInterval: 10000, // Update every 10 seconds for live data
    refetchIntervalInBackground: true,
    staleTime: 5000, // Consider data stale after 5 seconds
  });
};
