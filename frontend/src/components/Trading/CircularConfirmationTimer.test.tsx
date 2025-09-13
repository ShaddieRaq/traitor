import React from 'react';
import { ConfirmationStatus, TradingIntent } from '../../types';

interface CircularConfirmationTimerProps {
  confirmation: ConfirmationStatus;
  tradingIntent?: TradingIntent;
  className?: string;
}

const CircularConfirmationTimer: React.FC<CircularConfirmationTimerProps> = ({ 
  confirmation, 
  tradingIntent,
  className = '' 
}) => {
  
  // Simple test version - just show a basic circle
  return (
    <div className={`flex items-center space-x-3 ${className}`}>
      {/* Test Circle */}
      <div className="relative flex items-center">
        <svg className="transform -rotate-90 w-12 h-12">
          <circle
            cx="24"
            cy="24"
            r="20"
            stroke="currentColor"
            strokeWidth="3"
            fill="transparent"
            className="text-gray-200"
          />
          <circle
            cx="24"
            cy="24"
            r="20"
            stroke="currentColor"
            strokeWidth="3"
            fill="transparent"
            strokeDasharray="125.66"
            strokeDashoffset="62.83"
            className="stroke-blue-500 transition-all duration-1000"
            strokeLinecap="round"
          />
        </svg>
        
        <div className="absolute inset-0 flex items-center justify-center">
          <div className="text-center">
            <div className="text-xs">⏱️</div>
            <div className="text-xs font-bold text-blue-700">
              TEST
            </div>
          </div>
        </div>
      </div>

      <div className="flex-1 min-w-0">
        <div className="text-sm font-medium text-blue-700">
          Test Confirmation
        </div>
        <div className="text-xs text-gray-500">
          Debug mode
        </div>
      </div>
    </div>
  );
};

export default CircularConfirmationTimer;
