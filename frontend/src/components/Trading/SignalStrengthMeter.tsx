import React from 'react';
import { TradingIntent } from '../../types';
import Tooltip from '../ui/Tooltip';

interface SignalStrengthMeterProps {
  intent: TradingIntent;
  className?: string;
}

const SignalStrengthMeter: React.FC<SignalStrengthMeterProps> = ({ intent, className = '' }) => {
  const getActionColor = (action: string) => {
    switch (action) {
      case 'buy': return { stroke: 'stroke-green-500', text: 'text-green-700', bg: 'bg-green-50' };
      case 'sell': return { stroke: 'stroke-red-500', text: 'text-red-700', bg: 'bg-red-50' };
      default: return { stroke: 'stroke-blue-500', text: 'text-blue-700', bg: 'bg-blue-50' };
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
  
  // Circle progress calculations
  const radius = 20;
  const circumference = 2 * Math.PI * radius;
  const strengthOffset = circumference - (strengthPercentage / 100) * circumference;

  const tooltipText = `Signal Strength: Measures how strongly the combined technical indicators (RSI, Moving Averages, MACD) are pointing toward a specific trading action. Values range from 0-100% where higher percentages indicate stronger buy/sell signals based on market momentum and price patterns.`;

  return (
    <div className={`flex items-center space-x-3 ${className}`}>
      {/* Circular Signal Strength */}
      <Tooltip content={tooltipText}>
        <div className="relative flex items-center cursor-help">
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
      </Tooltip>

      {/* Compact info */}
      <div className="flex-1 min-w-0">
        <div className={`text-sm font-medium ${colors.text}`}>
          Signal Strength
        </div>
        <div className="text-xs text-gray-500">
          {strengthPercentage.toFixed(0)}% power
        </div>
        {intent.signal_strength >= 0.8 && intent.confidence >= 0.8 && (
          <div className="text-xs text-green-600 font-medium">🚀 Strong signal</div>
        )}
      </div>
    </div>
  );
};

export default SignalStrengthMeter;
