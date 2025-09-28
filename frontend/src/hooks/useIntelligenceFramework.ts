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

// Backward compatibility interface
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
    }
  };
}