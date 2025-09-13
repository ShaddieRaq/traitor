import { useQuery } from '@tanstack/react-query';
import api from '../lib/api';

export interface MarketAnalysisCandidate {
  product_id: string;
  base_name: string;
  price: number;
  volume_24h_million: number;
  price_change_24h: number;
  volume_change_24h: number;
  position_tokens: number;
  liquidity_score: number;
  volatility_score: number;
  momentum_score: number;
  risk_score: number;
  total_score: number;
  risk_level: string;
  risk_color: string;
  recommendation: string;
  recommendation_color: string;
  analysis: {
    liquidity_analysis: string;
    volatility_analysis: string;
    momentum_analysis: string;
    position_analysis: string;
  };
}

export interface MarketAnalysisResponse {
  candidates: MarketAnalysisCandidate[];
  summary: {
    top_recommendation?: MarketAnalysisCandidate;
    runner_ups?: MarketAnalysisCandidate[];
    counts: {
      highly_recommended: number;
      good_candidates: number;
      total_analyzed: number;
    };
    best_by_category: {
      liquidity: { product_id: string; volume: number };
      volatility: { product_id: string; change: number };
      momentum: { product_id: string; growth: number };
    };
  };
  excluded_pairs: string[];
  active_bots_count: number;
  timestamp: string;
  total_analyzed: number;
}

export const useMarketAnalysis = (limit: number = 15) => {
  return useQuery({
    queryKey: ['market-analysis', limit],
    queryFn: async () => {
      const response = await api.get(`/market-analysis/analysis?limit=${limit}`);
      return response.data as MarketAnalysisResponse;
    },
    refetchInterval: 60000, // Refresh every minute
    staleTime: 30000, // Consider data stale after 30 seconds
  });
};

export const useSinglePairAnalysis = (productId: string) => {
  return useQuery({
    queryKey: ['market-analysis', 'single', productId],
    queryFn: async () => {
      const response = await api.get(`/market-analysis/analysis/${productId}`);
      return response.data;
    },
    enabled: !!productId,
  });
};

export const usePairComparison = (pairs: string[]) => {
  const pairString = pairs.join(',');
  
  return useQuery({
    queryKey: ['market-analysis', 'comparison', pairString],
    queryFn: async () => {
      const response = await api.get(`/market-analysis/comparison?pairs=${pairString}`);
      return response.data;
    },
    enabled: pairs.length > 0,
  });
};
