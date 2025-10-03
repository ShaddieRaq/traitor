import { useQuery } from '@tanstack/react-query';

interface TrendAnalysis {
  product_id: string;
  trend_strength: number;
  confidence: number;
  regime: string;
  moving_average_alignment: 'BULLISH' | 'BEARISH' | 'NEUTRAL';
  volume_confirmation: boolean;
  analysis_timestamp: string;
  cache_ttl_seconds: number;
  timeframe_analysis: {
    short_term: {
      momentum: number;
      timeframe_name: string;
      price_change_pct: number;
    };
    medium_term: {
      momentum: number;
      timeframe_name: string;
      price_change_pct: number;
    };
    long_term: {
      momentum: number;
      timeframe_name: string;
      price_change_pct: number;
    };
  };
}

const fetchTrendAnalysis = async (productId: string): Promise<TrendAnalysis> => {
  const response = await fetch(`/api/v1/trends/${productId}`);
  
  if (!response.ok) {
    throw new Error(`Failed to fetch trend analysis for ${productId}`);
  }
  
  return response.json();
};

export const useTrendAnalysis = (productId: string) => {
  return useQuery({
    queryKey: ['trends', productId],
    queryFn: () => fetchTrendAnalysis(productId),
    refetchInterval: 60000, // Refresh every minute (trends change slower than prices)
    staleTime: 30000, // Consider data stale after 30 seconds
    enabled: !!productId,
  });
};

// Hook for Bitcoin trend (main market indicator)
export const useBitcoinTrend = () => {
  return useTrendAnalysis('BTC-USD');
};

// Utility function to get directional indicator
export const getTrendDirection = (trendStrength: number, maAlignment: string): {
  direction: 'UP' | 'DOWN' | 'SIDEWAYS';
  emoji: string;
  color: string;
} => {
  // Trend strength: -1.0 to +1.0 (negative = down, positive = up)
  // MA alignment: BULLISH/BEARISH/NEUTRAL
  
  if (Math.abs(trendStrength) < 0.1) {
    return {
      direction: 'SIDEWAYS',
      emoji: '↔️',
      color: 'text-gray-600'
    };
  }
  
  if (trendStrength > 0 && maAlignment === 'BULLISH') {
    return {
      direction: 'UP',
      emoji: '📈',
      color: 'text-green-600'
    };
  }
  
  if (trendStrength < 0 && maAlignment === 'BEARISH') {
    return {
      direction: 'DOWN',
      emoji: '📉',
      color: 'text-red-600'
    };
  }
  
  // Mixed signals - use trend strength as primary indicator
  if (trendStrength > 0) {
    return {
      direction: 'UP',
      emoji: '📈',
      color: 'text-green-600'
    };
  } else {
    return {
      direction: 'DOWN',
      emoji: '📉',
      color: 'text-red-600'
    };
  }
};

// Utility function to format regime with direction
export const getRegimeDisplay = (regime: string, direction: 'UP' | 'DOWN' | 'SIDEWAYS'): string => {
  switch (regime) {
    case 'STRONG_TRENDING':
      return `STRONG ${direction}TREND`;
    case 'TRENDING':
      return `${direction}TREND`;
    case 'RANGING':
      return 'RANGING';
    case 'CHOPPY':
      return 'CHOPPY';
    default:
      return regime;
  }
};