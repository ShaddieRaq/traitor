import React from 'react';
import { useBots } from '../hooks/useBots';

export const SimpleLearningStatus: React.FC = () => {
  const { data: bots, isLoading } = useBots();

  if (isLoading) return <div className="text-center py-4">Loading...</div>;

  if (!bots) return <div className="text-center py-4 text-red-600">No bot data</div>;

  // Count learning bots (weights different from defaults: RSI=0.4, MA=0.35, MACD=0.25)
  const learningBots = bots.filter(bot => {
    const config = bot.signal_config || {};
    const rsi = config.rsi?.weight || 0.4;
    const ma = config.moving_average?.weight || 0.35;
    const macd = config.macd?.weight || 0.25;
    
    return Math.abs(rsi - 0.4) > 0.01 || Math.abs(ma - 0.35) > 0.01 || Math.abs(macd - 0.25) > 0.01;
  }).length;

  const isUniversal = learningBots === bots.length && bots.length > 0;

  return (
    <div className={`p-6 rounded-lg border-4 ${isUniversal ? 'bg-green-50 border-green-500' : 'bg-red-50 border-red-500'}`}>
      <div className="text-center">
        <div className={`text-6xl font-bold mb-4 ${isUniversal ? 'text-green-600' : 'text-red-600'}`}>
          {learningBots}/{bots.length}
        </div>
        <div className="text-2xl font-bold mb-2">
          {isUniversal ? '✅ UNIVERSAL LEARNING ACTIVE' : '❌ NOT ALL BOTS LEARNING'}
        </div>
        <div className="text-lg text-gray-700">
          {isUniversal ? 'All bots have modified signal weights' : `Only ${learningBots} bots have learning weights`}
        </div>
        
        {/* Show first 3 bots as proof */}
        <div className="mt-4 text-sm">
          <div className="font-semibold mb-2">Proof (first 3 bots):</div>
          {bots.slice(0, 3).map(bot => {
            const config = bot.signal_config || {};
            const rsi = config.rsi?.weight || 0.4;
            const ma = config.moving_average?.weight || 0.35;
            const macd = config.macd?.weight || 0.25;
            
            return (
              <div key={bot.id} className="text-xs mb-1">
                <strong>{bot.pair || `Bot-${bot.id}`}:</strong> RSI={rsi.toFixed(3)}, MA={ma.toFixed(3)}, MACD={macd.toFixed(3)}
                {(Math.abs(rsi - 0.4) > 0.01 || Math.abs(ma - 0.35) > 0.01 || Math.abs(macd - 0.25) > 0.01) ? 
                  ' ✅ LEARNING' : ' ❌ DEFAULT'}
              </div>
            );
          })}
        </div>
      </div>
    </div>
  );
};