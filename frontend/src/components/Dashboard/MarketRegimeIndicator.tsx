import React from 'react';
import { TrendingUp, Activity, AlertCircle, BarChart3 } from 'lucide-react';
import { DataFreshnessIndicator } from '../DataFreshnessIndicators';

interface MarketRegimeData {
  pair: string;
  regime: 'CHOPPY' | 'TRENDING' | 'STRONG_TRENDING' | 'VOLATILE';
  trend_strength: number;
  confidence: number;
  moving_average_alignment: 'BULLISH' | 'BEARISH' | 'NEUTRAL';
  volume_confirmation: boolean;
}

interface MarketRegimeIndicatorProps {
  data?: MarketRegimeData[];
  isLoading?: boolean;
  dataUpdatedAt?: number;
  className?: string;
}

/**
 * Market Regime Intelligence Indicator - Phase 5B
 * 
 * Prominent display of real-time market regime analysis across major pairs.
 * Provides immediate context for trading decisions and AI system behavior.
 */
export const MarketRegimeIndicator: React.FC<MarketRegimeIndicatorProps> = ({
  data = [],
  isLoading = false,
  dataUpdatedAt,
  className = ''
}) => {
  // Calculate overall market sentiment
  const getOverallSentiment = () => {
    if (!data.length) return { regime: 'UNKNOWN', confidence: 0, color: 'gray' };
    
    const regimeCounts = data.reduce((acc, item) => {
      acc[item.regime] = (acc[item.regime] || 0) + 1;
      return acc;
    }, {} as Record<string, number>);
    
    const dominantRegime = Object.entries(regimeCounts).sort(([,a], [,b]) => b - a)[0];
    const avgConfidence = data.reduce((sum, item) => sum + item.confidence, 0) / data.length;
    
    const regimeColors = {
      'CHOPPY': 'yellow',
      'TRENDING': 'green', 
      'STRONG_TRENDING': 'emerald',
      'VOLATILE': 'red',
      'UNKNOWN': 'gray'
    };
    
    return {
      regime: dominantRegime[0],
      confidence: avgConfidence,
      color: regimeColors[dominantRegime[0] as keyof typeof regimeColors] || 'gray',
      count: dominantRegime[1],
      total: data.length
    };
  };

  const getRegimeIcon = (regime: string) => {
    switch (regime) {
      case 'TRENDING': return <TrendingUp className="h-5 w-5" />;
      case 'STRONG_TRENDING': return <TrendingUp className="h-5 w-5" />;
      case 'CHOPPY': return <Activity className="h-5 w-5" />;
      case 'VOLATILE': return <AlertCircle className="h-5 w-5" />;
      default: return <BarChart3 className="h-5 w-5" />;
    }
  };

  const getRegimeDescription = (regime: string) => {
    switch (regime) {
      case 'TRENDING': return 'Markets showing clear directional movement';
      case 'STRONG_TRENDING': return 'Markets in strong directional trends';
      case 'CHOPPY': return 'Markets moving sideways with no clear trend';
      case 'VOLATILE': return 'Markets experiencing high volatility';
      default: return 'Market conditions being analyzed';
    }
  };

  const overall = getOverallSentiment();

  if (isLoading) {
    return (
      <div className={`
        bg-gradient-to-r from-gray-50 to-blue-50 
        rounded-xl border-2 border-gray-200 p-4
        animate-pulse ${className}
      `}>
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-3">
            <div className="w-6 h-6 bg-gray-300 rounded"></div>
            <div className="w-32 h-5 bg-gray-300 rounded"></div>
          </div>
          <div className="w-20 h-4 bg-gray-300 rounded"></div>
        </div>
      </div>
    );
  }

  return (
    <div className={`
      bg-gradient-to-r from-indigo-50 via-purple-50 to-blue-50
      rounded-xl border-2 border-indigo-200 shadow-lg hover:shadow-xl transition-all duration-300
      ${className}
    `}>
      {/* Main Regime Display */}
      <div className="p-4">
        <div className="flex items-center justify-between mb-3">
          <div className="flex items-center space-x-3">
            <div className={`
              p-2 rounded-lg 
              ${overall.color === 'yellow' ? 'bg-yellow-100 text-yellow-700' :
                overall.color === 'green' ? 'bg-green-100 text-green-700' :
                overall.color === 'emerald' ? 'bg-emerald-100 text-emerald-700' :
                overall.color === 'red' ? 'bg-red-100 text-red-700' :
                'bg-gray-100 text-gray-700'}
            `}>
              {getRegimeIcon(overall.regime)}
            </div>
            <div>
              <div className="flex items-center space-x-2">
                <h3 className="text-lg font-bold text-gray-900">
                  Market Regime: {overall.regime}
                </h3>
                <span className="text-sm text-gray-600">
                  ({overall.count}/{overall.total} pairs)
                </span>
              </div>
              <p className="text-sm text-gray-600">
                {getRegimeDescription(overall.regime)}
              </p>
            </div>
          </div>
          
          <div className="text-right">
            <div className="text-lg font-bold text-indigo-700">
              {(overall.confidence * 100).toFixed(0)}%
            </div>
            <div className="text-xs text-gray-500">Confidence</div>
          </div>
        </div>

        {/* Individual Pair Breakdown */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-3 mb-3">
          {data.slice(0, 6).map((pair) => (
            <div 
              key={pair.pair} 
              className="bg-white bg-opacity-60 rounded-lg p-3 border border-white shadow-sm"
            >
              <div className="flex items-center justify-between mb-1">
                <span className="text-sm font-semibold text-gray-900">
                  {pair.pair}
                </span>
                <span className={`text-xs px-2 py-1 rounded-full font-semibold ${
                  pair.regime === 'CHOPPY' ? 'bg-yellow-100 text-yellow-800' :
                  pair.regime === 'TRENDING' ? 'bg-green-100 text-green-800' :
                  pair.regime === 'STRONG_TRENDING' ? 'bg-emerald-100 text-emerald-800' :
                  'bg-red-100 text-red-800'
                }`}>
                  {pair.regime}
                </span>
              </div>
              <div className="flex items-center justify-between text-xs text-gray-600">
                <span>
                  {pair.moving_average_alignment === 'BULLISH' ? '📈' : 
                   pair.moving_average_alignment === 'BEARISH' ? '📉' : '➡️'} 
                  {pair.moving_average_alignment}
                </span>
                <span>{(pair.confidence * 100).toFixed(0)}%</span>
              </div>
            </div>
          ))}
        </div>

        {/* Data Freshness Indicator */}
        <div className="flex items-center justify-between pt-2 border-t border-indigo-200">
          <div className="text-xs text-gray-600">
            🤖 AI Market Analysis • Updated every 5 minutes
          </div>
          {dataUpdatedAt && (
            <DataFreshnessIndicator 
              lastUpdated={new Date(dataUpdatedAt)} 
              freshThresholdSeconds={300}
              staleThresholdSeconds={600}
              size="sm"
            />
          )}
        </div>
      </div>
    </div>
  );
};

export default MarketRegimeIndicator;