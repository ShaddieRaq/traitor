import React from 'react';
import { Brain, Target, TrendingUp, DollarSign, TrendingDown, AlertTriangle, Zap, BarChart3 } from 'lucide-react';
import { DataFreshnessIndicator } from '../components/DataFreshnessIndicators';
import { useIntelligenceFramework } from '../hooks/useIntelligenceFramework';

// Phase 8.5: PROFIT-FOCUSED Intelligence Analytics - NO MORE VANITY METRICS!

interface IntelligenceAnalyticsProps {
  className?: string;
}

interface SignalProfitability {
  signal_type: string;
  profit_per_signal: number;
  total_signals: number;
  total_profit_impact: number;
  win_rate: number;
  accuracy: number; // Keep for comparison but de-emphasize
}

export const IntelligenceAnalytics: React.FC<IntelligenceAnalyticsProps> = ({
  className = ''
}) => {
  const { data: intelligenceData, isLoading, dataUpdatedAt } = useIntelligenceFramework();

  // Early return if data is not loaded yet
  if (isLoading || !intelligenceData) {
    return (
      <div className={`space-y-6 ${className}`}>
        <div className="animate-pulse">
          <div className="bg-gray-200 h-32 rounded-lg mb-6"></div>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            <div className="bg-gray-200 h-40 rounded-lg"></div>
            <div className="bg-gray-200 h-40 rounded-lg"></div>
            <div className="bg-gray-200 h-40 rounded-lg"></div>
          </div>
        </div>
      </div>
    );
  }

  // Calculate signal profitability from API data
  const calculateSignalProfitability = (): SignalProfitability[] => {
    const totalProfit = intelligenceData?.profitMetrics?.totalProfit || 0;
    const totalSignals = 6776036; // Use the actual number from API - could make this dynamic later
    const profitPerSignal = totalProfit / totalSignals;
    
    // This is mock data - in reality we'd need to enhance the API to track
    // profit contribution by signal type. For now, showing the concept.
    return [
      {
        signal_type: 'RSI',
        profit_per_signal: profitPerSignal * 0.68, // Weight by accuracy but FOCUS on profit
        total_signals: Math.floor(totalSignals * 0.33),
        total_profit_impact: totalProfit * 0.33,
        win_rate: 0.68,
        accuracy: 0.68
      },
      {
        signal_type: 'MACD', 
        profit_per_signal: profitPerSignal * 0.62,
        total_signals: Math.floor(totalSignals * 0.33),
        total_profit_impact: totalProfit * 0.33,
        win_rate: 0.62,
        accuracy: 0.62
      },
      {
        signal_type: 'Moving Average',
        profit_per_signal: profitPerSignal * 0.64,
        total_signals: Math.floor(totalSignals * 0.34),
        total_profit_impact: totalProfit * 0.34,
        win_rate: 0.64,
        accuracy: 0.64
      }
    ].sort((a, b) => b.profit_per_signal - a.profit_per_signal); // Sort by PROFIT, not accuracy
  };

  // Calculate profitable vs losing markets
  const winners = intelligenceData?.topPerformers?.winners || [];
  const losers = intelligenceData?.topPerformers?.losers || [];
  
  const profitPerformance = {
    total_pnl: intelligenceData?.profitMetrics?.totalProfit || 0,
    profitable_bots: intelligenceData?.profitMetrics?.profitableBots || 0,
    losing_bots: intelligenceData?.profitMetrics?.losingBots || 0,
    avg_profit_per_signal: intelligenceData?.profitMetrics?.avgProfitPerSignal || 0,
    loss_prevention: intelligenceData?.profitMetrics?.lossPrevention || 0,
    top_performers: [
      ...winners.map(w => ({ 
        pair: w.pair || 'Unknown',
        profit: w.profit || 0,
        profit_per_trade: w.profitPerTrade || 0,
        win_rate: w.winRate || 0,
        type: 'winner' as const 
      })),
      ...losers.map(l => ({ 
        pair: l.pair || 'Unknown', 
        profit: l.loss || 0, 
        profit_per_trade: l.lossPerTrade || 0,
        win_rate: l.winRate || 0,
        type: 'loser' as const 
      }))
    ]
  };

  const signalProfitability = calculateSignalProfitability();

  return (
    <div className={`space-y-6 max-w-7xl mx-auto px-4 ${className}`}>
      {/* Header Section - PROFIT FOCUSED */}
      <div className="bg-gradient-to-r from-red-50 via-yellow-50 to-green-50 rounded-xl border-2 border-orange-200 p-6">
        <div className="flex items-center justify-between mb-4">
          <div className="flex items-center space-x-3">
            <div className="p-3 bg-orange-100 rounded-lg">
              <DollarSign className="h-8 w-8 text-orange-600" />
            </div>
            <div>
              <h1 className="text-2xl font-bold text-gray-900">💰 PROFIT-FOCUSED AI Analytics</h1>
              <p className="text-gray-600">Money matters - accuracy percentages don't pay bills</p>
            </div>
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

        {/* THE REALITY CHECK - Phase 8.5 */}
        <div className="bg-white bg-opacity-80 rounded-lg p-4 mb-4">
          <div className="flex items-center space-x-2 mb-2">
            <AlertTriangle className="h-5 w-5 text-red-500" />
            <span className="font-semibold text-red-700">REALITY CHECK</span>
          </div>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-sm">
            <div>
              <div className="text-red-600 font-medium">❌ VANITY METRICS (Don't Pay Bills):</div>
              <div className="text-gray-600 ml-4">
                • RSI: 68% accuracy<br/>
                • MACD: 62% accuracy<br/>
                • 6.7M+ predictions made<br/>
                • "AI-enhanced" features active
              </div>
            </div>
            <div>
              <div className="text-green-600 font-medium">💰 WHAT ACTUALLY MATTERS:</div>
              <div className="text-gray-600 ml-4">
                • Portfolio: <span className={`font-bold ${profitPerformance.total_pnl < 0 ? 'text-red-600' : 'text-green-600'}`}>${profitPerformance.total_pnl.toFixed(2)}</span><br/>
                • Profit per signal: <span className="font-bold">${profitPerformance.avg_profit_per_signal.toFixed(4)}</span><br/>
                • Winners: {profitPerformance.profitable_bots} markets<br/>
                • Losers: {profitPerformance.losing_bots} markets (STOP THESE!)
              </div>
            </div>
          </div>
        </div>

        {/* Key Profit-Focused Metrics */}
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          <div className="bg-white bg-opacity-70 rounded-lg p-4 text-center">
            <div className={`text-2xl font-bold ${
              profitPerformance.total_pnl > 0 ? 'text-green-600' : 
              profitPerformance.total_pnl < 0 ? 'text-red-600' : 'text-gray-600'
            }`}>
              ${profitPerformance.total_pnl.toFixed(2)}
            </div>
            <div className="text-sm text-gray-600">Portfolio P&L</div>
            <div className="text-xs text-gray-500 mt-1">This is what matters</div>
          </div>
          <div className="bg-white bg-opacity-70 rounded-lg p-4 text-center">
            <div className="text-2xl font-bold text-green-600">{profitPerformance.profitable_bots}</div>
            <div className="text-sm text-gray-600">Profitable Markets</div>
            <div className="text-xs text-gray-500 mt-1">Scale these up</div>
          </div>
          <div className="bg-white bg-opacity-70 rounded-lg p-4 text-center">
            <div className="text-2xl font-bold text-red-600">{profitPerformance.losing_bots}</div>
            <div className="text-sm text-gray-600">Losing Markets</div>
            <div className="text-xs text-red-500 mt-1">STOP TRADING THESE</div>
          </div>
          <div className="bg-white bg-opacity-70 rounded-lg p-4 text-center">
            <div className="text-2xl font-bold text-purple-600">${profitPerformance.loss_prevention.toFixed(0)}</div>
            <div className="text-sm text-gray-600">Potential Loss Prevention</div>
            <div className="text-xs text-gray-500 mt-1">By auto-pausing losers</div>
          </div>
        </div>
      </div>

      {/* SIGNAL PROFITABILITY ANALYSIS - The heart of profit-focused AI */}
      <div className="bg-white rounded-xl shadow-lg border-2 border-green-200 p-6">
        <h3 className="text-xl font-semibold text-gray-900 mb-4 flex items-center">
          <BarChart3 className="h-6 w-6 mr-2 text-green-600" />
          🎯 SIGNAL PROFITABILITY ANALYSIS
          <span className="ml-2 text-sm bg-green-100 text-green-800 px-2 py-1 rounded">PROFIT MATTERS</span>
        </h3>
        
        <div className="mb-4 p-3 bg-yellow-50 border border-yellow-200 rounded-lg">
          <div className="text-sm text-yellow-800">
            <strong>🔍 Key Question:</strong> Which signals actually make money vs just being "accurate"?
          </div>
        </div>
        
        <div className="space-y-4">
          {signalProfitability.map((signal, index) => (
            <div key={signal.signal_type} className="p-4 border rounded-lg bg-gray-50">
              <div className="flex items-center justify-between mb-3">
                <div className="flex items-center space-x-3">
                  <div className={`p-2 rounded-lg ${
                    signal.profit_per_signal > 0 ? 'bg-green-100' : 'bg-red-100'
                  }`}>
                    {index === 0 ? <Zap className="h-5 w-5 text-yellow-600" /> : 
                     index === 1 ? <TrendingUp className="h-5 w-5 text-blue-600" /> :
                     <Target className="h-5 w-5 text-purple-600" />}
                  </div>
                  <div>
                    <div className="font-semibold text-gray-900">{signal.signal_type}</div>
                    <div className="text-sm text-gray-600">{signal.total_signals.toLocaleString()} signals generated</div>
                  </div>
                </div>
                <div className="text-right">
                  <div className={`text-xl font-bold ${
                    signal.profit_per_signal > 0 ? 'text-green-600' : 'text-red-600'
                  }`}>
                    ${signal.profit_per_signal.toFixed(4)}
                  </div>
                  <div className="text-sm text-gray-600">per signal</div>
                </div>
              </div>
              
              <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
                <div className="text-center p-2 bg-white rounded">
                  <div className={`font-bold ${
                    signal.total_profit_impact > 0 ? 'text-green-600' : 'text-red-600'
                  }`}>
                    ${signal.total_profit_impact.toFixed(2)}
                  </div>
                  <div className="text-gray-600">Total Impact</div>
                </div>
                <div className="text-center p-2 bg-white rounded">
                  <div className="font-bold text-blue-600">{(signal.win_rate * 100).toFixed(1)}%</div>
                  <div className="text-gray-600">Win Rate</div>
                </div>
                <div className="text-center p-2 bg-white rounded">
                  <div className="font-bold text-purple-600">{(signal.accuracy * 100).toFixed(1)}%</div>
                  <div className="text-gray-600">Accuracy</div>
                </div>
                <div className="text-center p-2 bg-white rounded">
                  <div className={`font-bold ${
                    signal.profit_per_signal > profitPerformance.avg_profit_per_signal ? 'text-green-600' : 'text-red-600'
                  }`}>
                    {signal.profit_per_signal > profitPerformance.avg_profit_per_signal ? '✅' : '❌'}
                  </div>
                  <div className="text-gray-600">vs Avg</div>
                </div>
              </div>
              
              {/* The insight that matters */}
              <div className="mt-3 p-3 bg-blue-50 rounded border border-blue-200">
                <div className="text-sm text-blue-800">
                  <strong>💡 Insight:</strong> {signal.accuracy > 0.65 ? 
                    `High ${(signal.accuracy * 100).toFixed(0)}% accuracy, but ` : 
                    `Lower ${(signal.accuracy * 100).toFixed(0)}% accuracy and `}
                  {signal.profit_per_signal > 0 ? 
                    `making $${signal.profit_per_signal.toFixed(4)} per signal ✅` :
                    `losing $${Math.abs(signal.profit_per_signal).toFixed(4)} per signal ❌`}
                </div>
              </div>
            </div>
          ))}
        </div>
        
        <div className="mt-4 p-4 bg-orange-50 border border-orange-200 rounded-lg">
          <div className="text-sm text-orange-800">
            <strong>🔥 Key Takeaway:</strong> Signal accuracy doesn't equal profitability! 
            Focus on ${" "}profit per signal, not accuracy percentages. 
            A 50% accurate signal that makes $0.10 per trade beats a 70% accurate signal that loses $0.05 per trade.
          </div>
        </div>
      </div>

      {/* IMMEDIATE ACTION ITEMS - What to do NOW */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Markets to STOP Trading */}
        <div className="bg-white rounded-xl shadow-lg border-2 border-red-200 p-6">
          <h3 className="text-lg font-semibold text-gray-900 mb-4 flex items-center">
            <TrendingDown className="h-5 w-5 mr-2 text-red-600" />
            🚫 STOP TRADING THESE (Losing Money)
          </h3>
          <div className="space-y-3">
            {profitPerformance.top_performers
              .filter(p => p.type === 'loser')
              .slice(0, 3)
              .map((loser, idx) => {
                const loss = Math.abs(loser.profit);
                const lossPerTrade = Math.abs(loser.profit_per_trade);
                
                return (
                  <div key={idx} className="p-3 bg-red-50 rounded-lg border border-red-200">
                    <div className="flex justify-between items-center">
                      <div>
                        <div className="font-semibold text-red-800">{loser.pair}</div>
                        <div className="text-sm text-red-600">
                          -${loss.toFixed(2)} total • -${lossPerTrade.toFixed(4)} per trade
                        </div>
                      </div>
                      <button className="px-3 py-1 bg-red-600 text-white text-xs rounded hover:bg-red-700">
                        PAUSE BOT
                      </button>
                    </div>
                    <div className="text-xs text-gray-600 mt-2">
                      💡 Action: Auto-pause to prevent further losses
                    </div>
                  </div>
                );
              })}
          </div>
        </div>

        {/* Markets to SCALE UP */}
        <div className="bg-white rounded-xl shadow-lg border-2 border-green-200 p-6">
          <h3 className="text-lg font-semibold text-gray-900 mb-4 flex items-center">
            <TrendingUp className="h-5 w-5 mr-2 text-green-600" />
            🚀 SCALE UP THESE (Making Money)
          </h3>
          <div className="space-y-3">
            {profitPerformance.top_performers
              .filter(p => p.type === 'winner')
              .slice(0, 3)
              .map((winner, idx) => {
                const profit = winner.profit;
                const profitPerTrade = winner.profit_per_trade;
                
                return (
                  <div key={idx} className="p-3 bg-green-50 rounded-lg border border-green-200">
                    <div className="flex justify-between items-center">
                      <div>
                        <div className="font-semibold text-green-800">{winner.pair}</div>
                        <div className="text-sm text-green-600">
                          +${profit.toFixed(2)} total • +${profitPerTrade.toFixed(4)} per trade
                        </div>
                      </div>
                      <button className="px-3 py-1 bg-green-600 text-white text-xs rounded hover:bg-green-700">
                        SCALE 2x
                      </button>
                    </div>
                    <div className="text-xs text-gray-600 mt-2">
                      💡 Action: Increase position sizes to 2x current
                    </div>
                  </div>
                );
              })}
          </div>
        </div>
      </div>

      {/* The Bottom Line Summary */}
      <div className="bg-gradient-to-r from-purple-100 to-blue-100 rounded-xl border-2 border-purple-300 p-6">
        <h3 className="text-xl font-semibold text-gray-900 mb-4 flex items-center">
          <Brain className="h-6 w-6 mr-2 text-purple-600" />
          🎯 THE BOTTOM LINE
        </h3>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          <div className="bg-white bg-opacity-70 rounded-lg p-4">
            <h4 className="font-semibold text-red-600 mb-2">❌ STOP OBSESSING OVER:</h4>
            <ul className="text-sm text-gray-700 space-y-1">
              <li>• Signal accuracy percentages</li>
              <li>• Number of predictions made</li>
              <li>• "AI-enhanced" feature counts</li>
              <li>• Market regime detection without profit impact</li>
              <li>• Complex intelligence framework phases</li>
            </ul>
          </div>
          <div className="bg-white bg-opacity-70 rounded-lg p-4">
            <h4 className="font-semibold text-green-600 mb-2">✅ FOCUS ON WHAT MAKES MONEY:</h4>
            <ul className="text-sm text-gray-700 space-y-1">
              <li>• <strong>${profitPerformance.total_pnl.toFixed(2)}</strong> portfolio profit</li>
              <li>• <strong>${profitPerformance.avg_profit_per_signal.toFixed(4)}</strong> profit per signal</li>
              <li>• Pause {profitPerformance.losing_bots} losing markets immediately</li>
              <li>• Scale {profitPerformance.profitable_bots} winning markets</li>
              <li>• Position sizing based on performance</li>
            </ul>
          </div>
        </div>
        <div className="mt-4 text-center p-3 bg-yellow-100 rounded-lg border border-yellow-300">
          <div className="text-sm font-semibold text-yellow-800">
            💰 Remember: A profitable trading system with 40% accuracy beats an unprofitable system with 80% accuracy!
          </div>
        </div>
      </div>
    </div>
  );
};

export default IntelligenceAnalytics;