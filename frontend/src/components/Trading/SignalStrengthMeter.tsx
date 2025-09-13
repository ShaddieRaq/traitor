import React from 'react';
import { TradingIntent } from '../../types';

interface SignalStrengthMeterProps {
  intent: TradingIntent;
  className?: string;
}

const SignalStrengthMeter: React.FC<SignalStrengthMeterProps> = ({ intent, className = '' }) => {
  const getActionColor = (action: string) => {
    switch (action) {
      case 'buy': return { stroke: 'stroke-green-500', text: 'text-green-700', bg: 'bg-green-50' };
      case 'sell': return { stroke: 'stroke-red-500', text: 'text-red-700', bg: 'bg-red-50' };
      default: return { stroke: 'stroke-gray-400', text: 'text-gray-700', bg: 'bg-gray-50' };
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
  
  // Circle progress calculations
  const radius = 20;
  const circumference = 2 * Math.PI * radius;
  const strengthOffset = circumference - (strengthPercentage / 100) * circumference;

  return (
    <div className={`flex items-center space-x-3 ${className}`}>
      {/* Circular Signal Strength */}
      <div className="relative flex items-center">
        <svg className="transform -rotate-90 w-12 h-12">
          {/* Background circle */}
          <circle
            cx="24"
            cy="24"
            r={radius}
            stroke="currentColor"
            strokeWidth="3"
            fill="transparent"
            className="text-gray-200"
          />
          {/* Signal strength progress */}
          <circle
            cx="24"
            cy="24"
            r={radius}
            stroke="currentColor"
            strokeWidth="3"
            fill="transparent"
            strokeDasharray={circumference}
            strokeDashoffset={strengthOffset}
            className={`${colors.stroke} transition-all duration-500`}
            strokeLinecap="round"
          />
        </svg>
        {/* Center icon and percentage */}
        <div className="absolute inset-0 flex items-center justify-center">
          <div className="text-center">
            <div className="text-xs">{getActionIcon(intent.next_action)}</div>
            <div className={`text-xs font-bold ${colors.text}`}>
              {strengthPercentage.toFixed(0)}%
            </div>
          </div>
        </div>
      </div>

      {/* Compact info */}
      <div className="flex-1 min-w-0">
        <div className={`text-sm font-medium ${colors.text}`}>
          {intent.next_action.toUpperCase()}
        </div>
        <div className="text-xs text-gray-500">
          {confidencePercentage.toFixed(0)}% confidence
        </div>
        {intent.signal_strength >= 0.8 && intent.confidence >= 0.8 && (
          <div className="text-xs text-green-600 font-medium">🚀 Strong signal</div>
        )}
      </div>
    </div>
  );
};

export default SignalStrengthMeter;
