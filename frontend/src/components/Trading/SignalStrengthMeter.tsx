import React from 'react';
import { TradingIntent } from '../../types';

interface SignalStrengthMeterProps {
  intent: TradingIntent;
  className?: string;
}

const SignalStrengthMeter: React.FC<SignalStrengthMeterProps> = ({ intent, className = '' }) => {
  const getActionColor = (action: string) => {
    switch (action) {
      case 'buy': return { bg: 'bg-green-500', text: 'text-green-700', light: 'bg-green-100' };
      case 'sell': return { bg: 'bg-red-500', text: 'text-red-700', light: 'bg-red-100' };
      default: return { bg: 'bg-gray-400', text: 'text-gray-700', light: 'bg-gray-100' };
    }
  };

  const getActionIcon = (action: string) => {
    switch (action) {
      case 'buy': return '📈';
      case 'sell': return '📉';
      default: return '⏸️';
    }
  };

  const colors = getActionColor(intent.next_action);
  const strengthPercentage = intent.signal_strength * 100;
  const confidencePercentage = intent.confidence * 100;

  return (
    <div className={`${className}`}>
      <div className="flex items-center justify-between mb-2">
        <div className="flex items-center space-x-2">
          <span className="text-lg">{getActionIcon(intent.next_action)}</span>
          <span className={`text-sm font-medium ${colors.text}`}>
            {intent.next_action.toUpperCase()}
          </span>
        </div>
        <div className="text-xs text-gray-500">
          {strengthPercentage.toFixed(0)}% strength
        </div>
      </div>

      {/* Signal Strength Bar */}
      <div className="mb-2">
        <div className="flex justify-between text-xs text-gray-500 mb-1">
          <span>Signal Strength</span>
          <span>{strengthPercentage.toFixed(1)}%</span>
        </div>
        <div className="w-full bg-gray-200 rounded-full h-2">
          <div 
            className={`h-2 rounded-full transition-all duration-500 ${colors.bg}`}
            style={{ width: `${strengthPercentage}%` }}
          ></div>
        </div>
      </div>

      {/* Confidence Bar */}
      <div className="mb-2">
        <div className="flex justify-between text-xs text-gray-500 mb-1">
          <span>Confidence</span>
          <span>{confidencePercentage.toFixed(1)}%</span>
        </div>
        <div className="w-full bg-gray-200 rounded-full h-1.5">
          <div 
            className={`h-1.5 rounded-full transition-all duration-500 ${colors.bg} opacity-75`}
            style={{ width: `${confidencePercentage}%` }}
          ></div>
        </div>
      </div>

      {/* Distance to Threshold */}
      {intent.distance_to_threshold > 0 && (
        <div className="text-xs text-gray-500 mt-1">
          Need {intent.distance_to_threshold.toFixed(3)} more to trigger
        </div>
      )}

      {/* Ready indicator */}
      {intent.signal_strength >= 0.8 && intent.confidence >= 0.8 && (
        <div className={`text-xs px-2 py-1 rounded mt-2 ${colors.light} ${colors.text} font-medium`}>
          🚀 Strong signal detected!
        </div>
      )}
    </div>
  );
};

export default SignalStrengthMeter;
