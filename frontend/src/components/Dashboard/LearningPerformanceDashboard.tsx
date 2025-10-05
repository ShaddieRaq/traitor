import React from 'react';
import { TrendingUp, TrendingDown, Brain, BarChart3, Target, Clock } from 'lucide-react';

interface LearningBotData {
  id: number;
  pair: string;
  pnlBefore: number;
  pnlAfter: number;
  strategy: string;
  timeActive: string;
  signalChanges: {
    rsi: { before: number; after: number };
    ma: { before: number; after: number };
    macd: { before: number; after: number };
  };
}

// Sample data based on our Phase 8 learning results
const LEARNING_PERFORMANCE_DATA: LearningBotData[] = [
  {
    id: 4,
    pair: "ETH-USD", 
    pnlBefore: -4.49,
    pnlAfter: -1.37,
    strategy: "Moderate Rebalance",
    timeActive: "8h",
    signalChanges: {
      rsi: { before: 40, after: 32 },
      ma: { before: 35, after: 35 },
      macd: { before: 25, after: 33 }
    }
  },
  {
    id: 14,
    pair: "AVAX-USD",
    pnlBefore: -5.67,
    pnlAfter: -4.96,
    strategy: "Aggressive Rebalance", 
    timeActive: "8h",
    signalChanges: {
      rsi: { before: 40, after: 25 },
      ma: { before: 40, after: 55 },
      macd: { before: 20, after: 20 }
    }
  },
  {
    id: 13,
    pair: "SUI-USD",
    pnlBefore: -11.00,
    pnlAfter: -10.62,
    strategy: "Aggressive Rebalance",
    timeActive: "8h", 
    signalChanges: {
      rsi: { before: 33.5, after: 23.5 },
      ma: { before: 31.2, after: 41.2 },
      macd: { before: 35.3, after: 35.3 }
    }
  },
  {
    id: 12,
    pair: "AERO-USD",
    pnlBefore: 1.23,
    pnlAfter: -1.06,
    strategy: "Winner Optimization",
    timeActive: "8h",
    signalChanges: {
      rsi: { before: 40, after: 38.1 },
      ma: { before: 40, after: 42.9 },
      macd: { before: 20, after: 19.0 }
    }
  }
];

export const LearningPerformanceDashboard: React.FC = () => {
  const totalImprovement = LEARNING_PERFORMANCE_DATA.reduce((sum, bot) => {
    return sum + (bot.pnlAfter - bot.pnlBefore);
  }, 0);

  const improvingBots = LEARNING_PERFORMANCE_DATA.filter(bot => bot.pnlAfter > bot.pnlBefore);
  const decliningBots = LEARNING_PERFORMANCE_DATA.filter(bot => bot.pnlAfter < bot.pnlBefore);

  return (
    <div className="bg-white rounded-xl shadow-lg border p-6">
      <div className="flex items-center justify-between mb-6">
        <div className="flex items-center space-x-3">
          <div className="p-2 bg-purple-100 rounded-lg">
            <Brain className="h-6 w-6 text-purple-600" />
          </div>
          <div>
            <h3 className="text-lg font-bold text-gray-900">Learning System Performance</h3>
            <p className="text-sm text-gray-600">Phase 8: Profit-Focused Learning Results</p>
          </div>
        </div>
        <div className="text-right">
          <div className={`text-2xl font-bold ${totalImprovement >= 0 ? 'text-green-600' : 'text-red-600'}`}>
            {totalImprovement >= 0 ? '+' : ''}${totalImprovement.toFixed(2)}
          </div>
          <div className="text-sm text-gray-600">Total Impact (8h)</div>
        </div>
      </div>

      {/* Summary Stats */}
      <div className="grid grid-cols-3 gap-4 mb-6">
        <div className="bg-green-50 rounded-lg p-4 border border-green-200">
          <div className="flex items-center space-x-2 mb-2">
            <TrendingUp className="h-4 w-4 text-green-600" />
            <span className="text-sm font-medium text-green-700">Improving</span>
          </div>
          <div className="text-2xl font-bold text-green-600">{improvingBots.length}</div>
          <div className="text-xs text-green-600">bots showing gains</div>
        </div>
        
        <div className="bg-red-50 rounded-lg p-4 border border-red-200">
          <div className="flex items-center space-x-2 mb-2">
            <TrendingDown className="h-4 w-4 text-red-600" />
            <span className="text-sm font-medium text-red-700">Declining</span>
          </div>
          <div className="text-2xl font-bold text-red-600">{decliningBots.length}</div>
          <div className="text-xs text-red-600">bots with losses</div>
        </div>

        <div className="bg-blue-50 rounded-lg p-4 border border-blue-200">
          <div className="flex items-center space-x-2 mb-2">
            <Clock className="h-4 w-4 text-blue-600" />
            <span className="text-sm font-medium text-blue-700">Time Active</span>
          </div>
          <div className="text-2xl font-bold text-blue-600">8h</div>
          <div className="text-xs text-blue-600">learning duration</div>
        </div>
      </div>

      {/* Individual Bot Performance */}
      <div className="space-y-4">
        <h4 className="text-md font-semibold text-gray-800 flex items-center">
          <BarChart3 className="h-4 w-4 mr-2" />
          Bot-by-Bot Analysis
        </h4>
        
        {LEARNING_PERFORMANCE_DATA.map((bot) => {
          const improvement = bot.pnlAfter - bot.pnlBefore;
          const isImproving = improvement > 0;
          
          return (
            <div key={bot.id} className="border rounded-lg p-4 hover:shadow-md transition-shadow">
              <div className="flex items-center justify-between mb-3">
                <div className="flex items-center space-x-3">
                  <div className="font-bold text-gray-900">{bot.pair}</div>
                  <span className={`px-2 py-1 rounded-full text-xs font-medium ${
                    bot.strategy === 'Aggressive Rebalance' ? 'bg-red-100 text-red-700' :
                    bot.strategy === 'Moderate Rebalance' ? 'bg-orange-100 text-orange-700' :
                    'bg-green-100 text-green-700'
                  }`}>
                    {bot.strategy}
                  </span>
                </div>
                <div className="text-right">
                  <div className={`text-lg font-bold ${isImproving ? 'text-green-600' : 'text-red-600'}`}>
                    {isImproving ? '+' : ''}${improvement.toFixed(2)}
                  </div>
                  <div className="text-xs text-gray-600">
                    ${bot.pnlBefore.toFixed(2)} → ${bot.pnlAfter.toFixed(2)}
                  </div>
                </div>
              </div>

              {/* Signal Weight Changes */}
              <div className="grid grid-cols-3 gap-3">
                <div className="text-center">
                  <div className="text-xs text-gray-600 mb-1">RSI Weight</div>
                  <div className="flex items-center justify-center space-x-2">
                    <span className="text-sm text-gray-500">{bot.signalChanges.rsi.before}%</span>
                    <span className="text-xs text-gray-400">→</span>
                    <span className={`text-sm font-bold ${
                      bot.signalChanges.rsi.after < bot.signalChanges.rsi.before ? 'text-red-600' : 'text-blue-600'
                    }`}>
                      {bot.signalChanges.rsi.after}%
                    </span>
                  </div>
                </div>
                
                <div className="text-center">
                  <div className="text-xs text-gray-600 mb-1">MA Weight</div>
                  <div className="flex items-center justify-center space-x-2">
                    <span className="text-sm text-gray-500">{bot.signalChanges.ma.before}%</span>
                    <span className="text-xs text-gray-400">→</span>
                    <span className={`text-sm font-bold ${
                      bot.signalChanges.ma.after > bot.signalChanges.ma.before ? 'text-green-600' : 'text-blue-600'
                    }`}>
                      {bot.signalChanges.ma.after}%
                    </span>
                  </div>
                </div>
                
                <div className="text-center">
                  <div className="text-xs text-gray-600 mb-1">MACD Weight</div>
                  <div className="flex items-center justify-center space-x-2">
                    <span className="text-sm text-gray-500">{bot.signalChanges.macd.before}%</span>
                    <span className="text-xs text-gray-400">→</span>
                    <span className={`text-sm font-bold ${
                      bot.signalChanges.macd.after > bot.signalChanges.macd.before ? 'text-green-600' : 'text-blue-600'
                    }`}>
                      {bot.signalChanges.macd.after}%
                    </span>
                  </div>
                </div>
              </div>
            </div>
          );
        })}
      </div>

      {/* Learning Insights */}
      <div className="mt-6 bg-gradient-to-r from-purple-50 to-blue-50 rounded-lg p-4 border border-purple-200">
        <h4 className="text-sm font-semibold text-purple-800 mb-2 flex items-center">
          <Target className="h-4 w-4 mr-2" />
          Learning Insights (8 hours)
        </h4>
        <div className="space-y-1 text-sm text-purple-700">
          <div>✅ <strong>ETH-USD breakthrough:</strong> $3.12 improvement with moderate RSI reduction</div>
          <div>📈 <strong>Learning validation:</strong> 3/4 bots showing positive trends</div>
          <div>🎯 <strong>Strategy effectiveness:</strong> Aggressive rebalancing working for major losers</div>
          <div>⏰ <strong>Timeline:</strong> Early results promising, 24-48h needed for full assessment</div>
        </div>
      </div>
    </div>
  );
};

export default LearningPerformanceDashboard;