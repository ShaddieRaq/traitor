import React from 'react';
import { TradingIntent } from '../../types';
import Tooltip from '../ui/Tooltip';

interface SignalConfidenceMeterProps {
  intent: TradingIntent;
  className?: string;
}

const SignalConfidenceMeter: React.FC<SignalConfidenceMeterProps> = ({ intent, className = '' }) => {
  const confidencePercentage = intent.confidence * 100;
  
  // Confidence color based on level
  const getConfidenceColor = (confidence: number) => {
    if (confidence >= 80) return { stroke: 'stroke-green-500', text: 'text-green-700' };
    if (confidence >= 60) return { stroke: 'stroke-yellow-500', text: 'text-yellow-700' };
    if (confidence >= 40) return { stroke: 'stroke-orange-500', text: 'text-orange-700' };
    return { stroke: 'stroke-red-500', text: 'text-red-700' };
  };

  const colors = getConfidenceColor(confidencePercentage);
  
  // Circle progress calculations
  const radius = 20;
  const circumference = 2 * Math.PI * radius;
  const confidenceOffset = circumference - (confidencePercentage / 100) * circumference;

  const tooltipText = `Confidence: Represents the statistical reliability and certainty of the current signal calculation. High confidence indicates clean market data with consistent indicator readings, while low confidence suggests market noise or conflicting signals that make the analysis less trustworthy.`;

  return (
    <div className={`flex items-center space-x-3 ${className}`}>
      {/* Circular Confidence Meter */}
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
          {/* Confidence progress */}
          <circle
            cx="24"
            cy="24"
            r={radius}
            stroke="currentColor"
            strokeWidth="3"
            fill="transparent"
            strokeDasharray={circumference}
            strokeDashoffset={confidenceOffset}
            className={`${colors.stroke} transition-all duration-500`}
            strokeLinecap="round"
          />
        </svg>
        {/* Center icon and percentage */}
        <div className="absolute inset-0 flex items-center justify-center">
          <div className="text-center">
            <div className="text-xs">🎯</div>
            <div className={`text-xs font-bold ${colors.text}`}>
              {confidencePercentage.toFixed(0)}%
            </div>
          </div>
        </div>
      </div>
      </Tooltip>

      {/* Compact info */}
      <div className="flex-1 min-w-0">
        <div className={`text-sm font-medium ${colors.text}`}>
          Confidence
        </div>
        <div className="text-xs text-gray-500">
          {confidencePercentage >= 80 ? 'High reliability' : 
           confidencePercentage >= 60 ? 'Good reliability' :
           confidencePercentage >= 40 ? 'Fair reliability' : 'Low reliability'}
        </div>
      </div>
    </div>
  );
};

export default SignalConfidenceMeter;
