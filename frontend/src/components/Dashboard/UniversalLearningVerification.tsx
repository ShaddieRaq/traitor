import React from 'react';
import { Brain, CheckCircle, XCircle } from 'lucide-react';
import { useBots } from '../../hooks/useBots';

/**
 * Universal Learning Verification Component
 * 
 * Shows proof that universal learning is active on all bots
 * Displays actual signal weights vs defaults for verification
 */
export const UniversalLearningVerification: React.FC = () => {
  const { data: botsData, isLoading } = useBots();

  if (isLoading) {
    return (
      <div className="bg-white rounded-xl shadow-lg border p-6 animate-pulse">
        <div className="h-6 bg-gray-200 rounded w-1/3 mb-4"></div>
        <div className="space-y-3">
          {[1, 2, 3, 4, 5].map((i) => (
            <div key={i} className="h-4 bg-gray-200 rounded"></div>
          ))}
        </div>
      </div>
    );
  }

  if (!botsData || botsData.length === 0) {
    return (
      <div className="bg-white rounded-xl shadow-lg border p-6">
        <h3 className="text-lg font-bold text-red-600 mb-2">❌ No Bot Data Available</h3>
        <p className="text-gray-600">Unable to verify universal learning system status.</p>
      </div>
    );
  }

  // Default signal weights (what they should be if learning is NOT active)
  const defaultWeights = { rsi: 0.4, ma: 0.35, macd: 0.25 };

  // Analyze each bot for learning modifications
  const botAnalysis = botsData.slice(0, 10).map((bot: any) => {
    const signalConfig = bot.signal_config || {};
    const rsiWeight = signalConfig.rsi?.weight || 0;
    const maWeight = signalConfig.moving_average?.weight || 0;
    const macdWeight = signalConfig.macd?.weight || 0;

    const hasModifiedRSI = Math.abs(rsiWeight - defaultWeights.rsi) > 0.01;
    const hasModifiedMA = Math.abs(maWeight - defaultWeights.ma) > 0.01;
    const hasModifiedMACD = Math.abs(macdWeight - defaultWeights.macd) > 0.01;

    const isLearningActive = hasModifiedRSI || hasModifiedMA || hasModifiedMACD;

    return {
      id: bot.id,
      pair: bot.pair || `Bot-${bot.id}`,
      weights: { rsi: rsiWeight, ma: maWeight, macd: macdWeight },
      modifications: { rsi: hasModifiedRSI, ma: hasModifiedMA, macd: hasModifiedMACD },
      isLearningActive
    };
  });

  const learningCount = botAnalysis.filter(bot => bot.isLearningActive).length;
  const totalCount = botAnalysis.length;
  const isUniversal = learningCount === totalCount && totalCount > 0;

  return (
    <div className="bg-white rounded-xl shadow-lg border p-6">
      {/* Header */}
      <div className="flex items-center justify-between mb-6">
        <div className="flex items-center space-x-3">
          <Brain className="h-6 w-6 text-purple-600" />
          <div>
            <h3 className="text-lg font-bold text-gray-900">Universal Learning Verification</h3>
            <p className="text-sm text-gray-600">Proof of signal weight modifications (First 10 bots)</p>
          </div>
        </div>
        <div className="text-right">
          <div className={`text-2xl font-bold ${isUniversal ? 'text-green-600' : 'text-red-600'}`}>
            {isUniversal ? '✅ ACTIVE' : '❌ PARTIAL'}
          </div>
          <div className="text-sm text-gray-600">{learningCount}/{totalCount} Learning</div>
        </div>
      </div>

      {/* Quick Stats */}
      <div className="grid grid-cols-3 gap-4 mb-6">
        <div className="bg-blue-50 rounded-lg p-3 text-center">
          <div className="text-xl font-bold text-blue-600">{totalCount}</div>
          <div className="text-sm text-blue-700">Bots Checked</div>
        </div>
        <div className="bg-green-50 rounded-lg p-3 text-center">
          <div className="text-xl font-bold text-green-600">{learningCount}</div>
          <div className="text-sm text-green-700">Learning Active</div>
        </div>
        <div className="bg-purple-50 rounded-lg p-3 text-center">
          <div className="text-xl font-bold text-purple-600">
            {Math.round((learningCount / totalCount) * 100)}%
          </div>
          <div className="text-sm text-purple-700">Coverage</div>
        </div>
      </div>

      {/* Bot Details Table */}
      <div className="overflow-x-auto">
        <table className="w-full text-sm">
          <thead>
            <tr className="border-b bg-gray-50">
              <th className="text-left p-3 font-semibold">Bot</th>
              <th className="text-center p-3 font-semibold">RSI Weight</th>
              <th className="text-center p-3 font-semibold">MA Weight</th>
              <th className="text-center p-3 font-semibold">MACD Weight</th>
              <th className="text-center p-3 font-semibold">Learning Status</th>
            </tr>
          </thead>
          <tbody>
            {botAnalysis.map((bot) => (
              <tr key={bot.id} className="border-b hover:bg-gray-50">
                <td className="p-3 font-medium">{bot.pair}</td>
                <td className="p-3 text-center">
                  <div className="flex items-center justify-center space-x-2">
                    <span className={`font-mono ${bot.modifications.rsi ? 'text-red-600 font-bold' : 'text-gray-500'}`}>
                      {bot.weights.rsi.toFixed(3)}
                    </span>
                    {bot.modifications.rsi && <span className="text-red-500 text-xs">✓</span>}
                  </div>
                  <div className="text-xs text-gray-400">vs 0.400</div>
                </td>
                <td className="p-3 text-center">
                  <div className="flex items-center justify-center space-x-2">
                    <span className={`font-mono ${bot.modifications.ma ? 'text-green-600 font-bold' : 'text-gray-500'}`}>
                      {bot.weights.ma.toFixed(3)}
                    </span>
                    {bot.modifications.ma && <span className="text-green-500 text-xs">✓</span>}
                  </div>
                  <div className="text-xs text-gray-400">vs 0.350</div>
                </td>
                <td className="p-3 text-center">
                  <div className="flex items-center justify-center space-x-2">
                    <span className={`font-mono ${bot.modifications.macd ? 'text-blue-600 font-bold' : 'text-gray-500'}`}>
                      {bot.weights.macd.toFixed(3)}
                    </span>
                    {bot.modifications.macd && <span className="text-blue-500 text-xs">✓</span>}
                  </div>
                  <div className="text-xs text-gray-400">vs 0.250</div>
                </td>
                <td className="p-3 text-center">
                  <div className="flex items-center justify-center">
                    {bot.isLearningActive ? (
                      <div className="flex items-center space-x-1 text-green-600">
                        <CheckCircle className="h-4 w-4" />
                        <span className="text-xs font-medium">Active</span>
                      </div>
                    ) : (
                      <div className="flex items-center space-x-1 text-red-600">
                        <XCircle className="h-4 w-4" />
                        <span className="text-xs font-medium">Default</span>
                      </div>
                    )}
                  </div>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {/* Legend */}
      <div className="mt-4 p-3 bg-gray-50 rounded-lg">
        <div className="text-xs text-gray-600">
          <strong>Legend:</strong> 
          <span className="ml-2">✓ = Weight modified from default</span>
          <span className="ml-4">Bold colors = Learning active</span>
          <span className="ml-4">Gray = Default weights (no learning)</span>
        </div>
      </div>

      {/* Summary Message */}
      <div className={`mt-4 p-3 rounded-lg ${isUniversal ? 'bg-green-50 border border-green-200' : 'bg-red-50 border border-red-200'}`}>
        <div className={`text-sm font-medium ${isUniversal ? 'text-green-800' : 'text-red-800'}`}>
          {isUniversal ? (
            <>🎉 Universal Learning System is ACTIVE! All {totalCount} checked bots have modified signal weights.</>
          ) : (
            <>⚠️ Universal Learning is PARTIAL. Only {learningCount} of {totalCount} bots have learning modifications.</>
          )}
        </div>
      </div>
    </div>
  );
};