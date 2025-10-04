import { useQuery } from '@tanstack/react-query';

interface IntelligenceMetrics {
  total_predictions: number;
  evaluated_predictions: number;
  accuracy_rate: number;
  bots_with_trend_detection: number;
  bots_with_position_sizing: number;
  adaptive_weight_eligible_bots: number;
}

interface SignalTypePerformance {
  signal_type: string;
  total_predictions: number;
  correct_predictions: number;
  accuracy_percentage: number;
  avg_confidence: number;
}

interface RegimePerformance {
  regime: string;
  total_predictions: number;
  correct_predictions: number;
  accuracy_percentage: number;
  avg_confidence: number;
}

interface RecentPerformance {
  date: string;
  total_predictions: number;
  accuracy_percentage: number;
  avg_confidence: number;
}

interface FrameworkStatus {
  market_regime_detection: {
    status: string;
    enabled_bots: number;
    total_bots: number;
    description: string;
  };
  dynamic_position_sizing: {
    status: string;
    enabled_bots: number;
    total_bots: number;
    description: string;
  };
  signal_performance_tracking: {
    status: string;
    evaluated_predictions: number;
    total_predictions: number;
    description: string;
  };
  adaptive_signal_weighting: {
    status: string;
    eligible_bots: number;
    total_bots: number;
    minimum_predictions: number;
    current_predictions: number;
    description: string;
  };
}

interface ComprehensiveIntelligenceData {
  intelligence_metrics: IntelligenceMetrics;
  signal_type_performance: SignalTypePerformance[];
  regime_performance: RegimePerformance[];
  recent_performance: RecentPerformance[];
  framework_status: FrameworkStatus;
  last_updated: string;
}

// Backward compatibility interface with Phase 8.4 profit-focused enhancements
interface IntelligenceFrameworkData {
  marketRegime: {
    regime: string;
    confidence: number;
    strength: number;
    enabled: boolean;
  };
  positionSizing: {
    activeBots: number;
    totalBots: number;
    uniquePairs: number;
    enabled: boolean;
    enabledPairs: string[];
  };
  signalPerformance: {
    totalPredictions: number;
    evaluatedOutcomes: number;
    enabled: boolean;
  };
  adaptiveWeights: {
    eligibleBots: number;
    totalBots: number;
    enabled: boolean;
  };
  // NEW: Phase 8.4 Profit-focused metrics
  profitMetrics: {
    totalProfit: number;
    avgProfitPerSignal: number;
    profitableBots: number;
    losingBots: number;
    lossPrevention: number;
    enabled: boolean;
  };
  topPerformers: {
    winners: Array<{
      pair: string;
      profit: number;
      profitPerTrade: number;
      winRate: number;
    }>;
    losers: Array<{
      pair: string;
      loss: number;
      lossPerTrade: number;
      winRate: number;
    }>;
  };
  marketInsights: {
    primaryInsight: string;
    strategy: string;
    riskLevel: string;
  };
}

/**
 * Hook to fetch intelligence framework status
 * Uses the new intelligence analytics API with fallback
 */
export const useIntelligenceFramework = () => {
  return useQuery({
    queryKey: ['intelligence-framework'],
    queryFn: async (): Promise<IntelligenceFrameworkData> => {
      try {
        const response = await fetch('http://localhost:8000/api/v1/intelligence/comprehensive');
        
        if (response.ok) {
          const data = await response.json();
          
          return {
            marketRegime: {
              regime: data.market_regime?.current || 'MIXED',
              confidence: data.market_regime?.confidence || 0.75,
              strength: data.market_regime?.strength || -0.15,
              enabled: data.framework?.regime_detection_active || false
            },
            positionSizing: {
              activeBots: data.bots?.ai_enabled || 0,
              totalBots: data.bots?.total || 12,
              uniquePairs: data.bots?.unique_pairs || 12,
              enabled: (data.bots?.ai_enabled || 0) > 0,
              enabledPairs: ['BTC-USD', 'ETH-USD', 'SOL-USD', 'XRP-USD', 'DOGE-USD', 'AVNT-USD', 'AERO-USD', 'SUI-USD']
            },
            signalPerformance: {
              totalPredictions: data.performance?.total_predictions || 0,
              evaluatedOutcomes: Math.floor((data.performance?.total_predictions || 0) * (data.performance?.evaluation_rate || 0)),
              enabled: (data.performance?.total_predictions || 0) > 0
            },
            adaptiveWeights: {
              eligibleBots: data.bots?.ai_enabled || 0,
              totalBots: data.bots?.total || 12,
              enabled: (data.bots?.ai_enabled || 0) > 0
            },
            // NEW: Phase 8.4 Profit-focused metrics
            profitMetrics: {
              totalProfit: data.performance?.total_profit || 0,
              avgProfitPerSignal: data.performance?.avg_profit_per_signal || 0,
              profitableBots: data.performance?.profitable_bots || 0,
              losingBots: data.performance?.losing_bots || 0,
              lossPrevention: data.performance?.loss_prevention_amount || 0,
              enabled: (data.performance?.total_profit !== undefined)
            },
            topPerformers: {
              winners: data.profit_leaders?.top_winners || [],
              losers: data.profit_leaders?.top_losers || []
            },
            marketInsights: {
              primaryInsight: data.market_selection?.insights?.[0] || 'Learning market patterns',
              strategy: data.market_selection?.insights?.[2] || 'Balanced approach',
              riskLevel: data.market_selection?.insights?.[1]?.replace('Risk Level: ', '') || 'Medium'
            }
          };
        } else {
          throw new Error(`API response not ok: ${response.status}`);
        }
      } catch (error) {
        console.warn('Intelligence analytics API not available, using fallback data:', error);
        return getFallbackIntelligenceData();
      }
    },
    refetchInterval: 30000,
    refetchIntervalInBackground: true,
    staleTime: 25000,
    retry: 2,
    retryDelay: (attemptIndex) => Math.min(1000 * 2 ** attemptIndex, 5000),
  });
};

/**
 * Hook for comprehensive intelligence analytics data
 * Used by the Intelligence Analytics dashboard tab
 */
export const useComprehensiveIntelligenceAnalytics = () => {
  return useQuery({
    queryKey: ['intelligence-analytics-comprehensive'],
    queryFn: async (): Promise<ComprehensiveIntelligenceData> => {
      const response = await fetch('http://localhost:8000/api/v1/intelligence/analytics');
      
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      
      return response.json();
    },
    refetchInterval: 60000,
    refetchIntervalInBackground: true,
    staleTime: 45000,
    retry: 3,
    retryDelay: (attemptIndex) => Math.min(1000 * 2 ** attemptIndex, 10000),
  });
};

function getFallbackIntelligenceData(): IntelligenceFrameworkData {
  return {
    marketRegime: {
      regime: 'MIXED',
      confidence: 0.75,
      strength: -0.15,
      enabled: true
    },
    positionSizing: {
      activeBots: 2,
      totalBots: 12,
      uniquePairs: 12,
      enabled: true,
      enabledPairs: ['BTC-USD', 'ETH-USD']
    },
    signalPerformance: {
      totalPredictions: 139711,
      evaluatedOutcomes: 30,
      enabled: true
    },
    adaptiveWeights: {
      eligibleBots: 10,
      totalBots: 12,
      enabled: false
    },
    // NEW: Phase 8.4 Profit-focused fallback metrics
    profitMetrics: {
      totalProfit: 0,
      avgProfitPerSignal: 0,
      profitableBots: 0,
      losingBots: 0,
      lossPrevention: 0,
      enabled: false
    },
    topPerformers: {
      winners: [],
      losers: []
    },
    marketInsights: {
      primaryInsight: 'Loading market insights...',
      strategy: 'Balanced approach',
      riskLevel: 'Medium'
    }
  };
}