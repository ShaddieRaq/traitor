import { useQuery } from '@tanstack/react-query';

interface MarketRegimeData {
  pair: string;
  regime: 'CHOPPY' | 'TRENDING' | 'STRONG_TRENDING' | 'VOLATILE';
  trend_strength: number;
  confidence: number;
  moving_average_alignment: 'BULLISH' | 'BEARISH' | 'NEUTRAL';
  volume_confirmation: boolean;
  analysis_timestamp: string;
}

interface TrendsApiResponse {
  pairs_analyzed: number;
  results: Record<string, {
    product_id: string;
    trend_strength: number;
    confidence: number;
    regime: string;
    moving_average_alignment: string;
    volume_confirmation: boolean;
    analysis_timestamp: string;
  }>;
  engine_stats: any;
}

const MAJOR_PAIRS = [
  'BTC-USD', 'ETH-USD', 'SOL-USD', 'XRP-USD', 'DOGE-USD', 'AVAX-USD'
];

const fetchMarketRegimeData = async (): Promise<MarketRegimeData[]> => {
  const pairsQuery = MAJOR_PAIRS.join(',');
  const response = await fetch(`http://localhost:8000/api/v1/trends/?pairs=${pairsQuery}`);
  
  if (!response.ok) {
    throw new Error(`HTTP error! status: ${response.status}`);
  }
  
  const data: TrendsApiResponse = await response.json();
  
  // Transform API response to component format
  return Object.entries(data.results).map(([pair, trendData]) => ({
    pair,
    regime: trendData.regime as 'CHOPPY' | 'TRENDING' | 'STRONG_TRENDING' | 'VOLATILE',
    trend_strength: trendData.trend_strength,
    confidence: trendData.confidence,
    moving_average_alignment: trendData.moving_average_alignment as 'BULLISH' | 'BEARISH' | 'NEUTRAL',
    volume_confirmation: trendData.volume_confirmation,
    analysis_timestamp: trendData.analysis_timestamp
  }));
};

export const useMarketRegimeData = () => {
  return useQuery({
    queryKey: ['market-regime-data'],
    queryFn: fetchMarketRegimeData,
    refetchInterval: 300000, // Refetch every 5 minutes (trend cache TTL)
    refetchIntervalInBackground: true,
    staleTime: 240000, // Consider data stale after 4 minutes
    retry: 3,
    retryDelay: (attemptIndex) => Math.min(1000 * 2 ** attemptIndex, 10000),
  });
};