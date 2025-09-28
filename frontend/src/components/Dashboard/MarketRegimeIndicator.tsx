import React, { useState } from 'react';
import { TrendingUp, Activity, AlertCircle, BarChart3, HelpCircle } from 'lucide-react';
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
  const [showHelp, setShowHelp] = useState(false);
  
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
                <button
                  className="p-1 rounded-full text-gray-400 hover:text-indigo-600 hover:bg-indigo-50 transition-colors duration-200"
                  title="Learn about market regimes"
                  onClick={() => setShowHelp(!showHelp)}
                >
                  <HelpCircle className="w-4 h-4" />
                </button>
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

        {/* Individual Pair Breakdown - All Pairs Dynamic */}
        {data.length > 0 ? (
          <div className="space-y-3 mb-3">
            {/* Summary Stats */}
            <div className="text-xs text-gray-600 flex items-center justify-between">
              <span>All Active Trading Pairs ({data.length} total)</span>
              <span className="text-blue-600 font-semibold">
                {data.filter(p => p.regime === 'TRENDING' || p.regime === 'STRONG_TRENDING').length} trending
              </span>
            </div>
            
            {/* Scrollable Grid for All Pairs */}
            <div className="max-h-64 overflow-y-auto">
              <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-2">
                {data
                  .sort((a, b) => {
                    // Sort by regime priority: STRONG_TRENDING > TRENDING > CHOPPY > VOLATILE
                    const regimeOrder = { 'STRONG_TRENDING': 0, 'TRENDING': 1, 'CHOPPY': 2, 'VOLATILE': 3 };
                    const aOrder = regimeOrder[a.regime as keyof typeof regimeOrder] ?? 99;
                    const bOrder = regimeOrder[b.regime as keyof typeof regimeOrder] ?? 99;
                    if (aOrder !== bOrder) return aOrder - bOrder;
                    // Secondary sort by confidence (descending)
                    return b.confidence - a.confidence;
                  })
                  .map((pair) => (
                  <div 
                    key={pair.pair} 
                    className="bg-white bg-opacity-60 rounded-lg p-2.5 border border-white shadow-sm hover:shadow-md transition-shadow"
                  >
                    <div className="flex items-center justify-between mb-1">
                      <span className="text-xs font-semibold text-gray-900 truncate">
                        {pair.pair}
                      </span>
                      <span className={`text-xs px-1.5 py-0.5 rounded-full font-semibold ${
                        pair.regime === 'CHOPPY' ? 'bg-yellow-100 text-yellow-800' :
                        pair.regime === 'TRENDING' ? 'bg-green-100 text-green-800' :
                        pair.regime === 'STRONG_TRENDING' ? 'bg-emerald-100 text-emerald-800' :
                        'bg-red-100 text-red-800'
                      }`}>
                        {pair.regime === 'STRONG_TRENDING' ? 'STRONG' : pair.regime}
                      </span>
                    </div>
                    <div className="flex items-center justify-between text-xs text-gray-600">
                      <span className="flex items-center space-x-1">
                        <span>
                          {pair.moving_average_alignment === 'BULLISH' ? '📈' : 
                           pair.moving_average_alignment === 'BEARISH' ? '📉' : '➡️'}
                        </span>
                        <span className="text-xs">
                          {pair.moving_average_alignment.slice(0, 4)}
                        </span>
                      </span>
                      <span className="font-semibold">{(pair.confidence * 100).toFixed(0)}%</span>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </div>
        ) : (
          <div className="text-center py-6 text-gray-500">
            <div className="text-sm">No market regime data available</div>
            <div className="text-xs mt-1">Waiting for AI analysis...</div>
          </div>
        )}

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

      {/* Help Modal */}
      {showHelp && (
        <div className="fixed inset-0 z-50 overflow-y-auto">
          <div className="flex items-center justify-center min-h-screen px-4 pt-4 pb-20 text-center sm:block sm:p-0">
            <div className="fixed inset-0 transition-opacity bg-gray-500 bg-opacity-75" onClick={() => setShowHelp(false)} />
            
            <div className="inline-block w-full max-w-2xl p-6 my-8 overflow-hidden text-left align-middle transition-all transform bg-white shadow-xl rounded-2xl">
              <div className="flex items-center justify-between mb-4">
                <h3 className="text-lg font-medium leading-6 text-gray-900">
                  Market Regime Analysis
                </h3>
                <button
                  onClick={() => setShowHelp(false)}
                  className="p-1 rounded-full hover:bg-gray-100 transition-colors"
                >
                  <AlertCircle className="w-5 h-5 text-gray-500" />
                </button>
              </div>

              <div className="space-y-6">
                <div className="border-b border-gray-200 pb-4">
                  <h4 className="text-md font-semibold text-gray-800 mb-2">
                    🎯 Regime Types
                  </h4>
                  <p className="text-sm text-gray-600 mb-3">
                    AI analyzes market behavior patterns to classify each trading pair into different regimes.
                  </p>
                  <div className="bg-gray-50 p-3 rounded-lg">
                    <p className="text-xs font-semibold text-gray-700 mb-2">Examples:</p>
                    <ul className="text-xs text-gray-600 space-y-1">
                      <li>• <strong>STRONG_TRENDING:</strong> Clear directional movement, tight thresholds</li>
                      <li>• <strong>TRENDING:</strong> Moderate directional bias, normal thresholds</li>
                      <li>• <strong>CHOPPY:</strong> Sideways movement, wide thresholds to avoid noise</li>
                      <li>• <strong>VOLATILE:</strong> High volatility, special handling required</li>
                    </ul>
                  </div>
                </div>

                <div>
                  <h4 className="text-md font-semibold text-gray-800 mb-2">
                    ⚙️ Trading Implications
                  </h4>
                  <p className="text-sm text-gray-600">
                    Each regime triggers different trading strategies and threshold adjustments to optimize performance and reduce false signals.
                  </p>
                </div>
              </div>

              <div className="mt-6 pt-4 border-t border-gray-200">
                <button
                  onClick={() => setShowHelp(false)}
                  className="w-full px-4 py-2 text-sm font-medium text-white bg-indigo-600 border border-transparent rounded-md hover:bg-indigo-700 focus:outline-none focus-visible:ring-2 focus-visible:ring-indigo-500 focus-visible:ring-offset-2 transition-colors"
                >
                  Got it!
                </button>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default MarketRegimeIndicator;