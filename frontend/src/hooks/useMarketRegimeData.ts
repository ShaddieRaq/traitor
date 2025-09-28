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

const fetchMarketRegimeData = async (): Promise<MarketRegimeData[]> => {
  // Use the enhanced bots API which already includes trend analysis for each bot
  const response = await fetch('http://localhost:8000/api/v1/bots/status/enhanced');
  
  if (!response.ok) {
    throw new Error(`HTTP error! status: ${response.status}`);
  }
  
  const bots = await response.json();
  
  // Transform enhanced bot data to market regime format
  return bots
    .filter((bot: any) => bot.status === 'RUNNING' && bot.trend_analysis)
    .map((bot: any) => ({
      pair: bot.pair,
      regime: bot.trend_analysis.regime as 'CHOPPY' | 'TRENDING' | 'STRONG_TRENDING' | 'VOLATILE',
      trend_strength: bot.trend_analysis.trend_strength,
      confidence: bot.trend_analysis.confidence,
      moving_average_alignment: bot.trend_analysis.moving_average_alignment as 'BULLISH' | 'BEARISH' | 'NEUTRAL',
      volume_confirmation: bot.trend_analysis.volume_confirmation,
      analysis_timestamp: bot.trend_analysis.analysis_timestamp
    }))
    .sort((a: MarketRegimeData, b: MarketRegimeData) => a.pair.localeCompare(b.pair)); // Sort alphabetically
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