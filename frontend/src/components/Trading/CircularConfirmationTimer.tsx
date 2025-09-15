import React from 'react';
import { ConfirmationStatus, TradingIntent } from '../../types';
import Tooltip from '../ui/Tooltip';

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
  
  // Simplified version to test rendering
  const isActive = confirmation.is_active;
  const action = confirmation.action || tradingIntent?.next_action || 'none';
  
  // Determine colors based on state
  const getColors = () => {
    if (isActive) {
      return action === 'buy' ? 'stroke-green-500 text-green-700' : 
             action === 'sell' ? 'stroke-red-500 text-red-700' : 
             'stroke-blue-500 text-blue-700';
    } else {
      return action === 'none' ? 'stroke-gray-400 text-gray-600' :
             action === 'suspended_cooldown' ? 'stroke-blue-400 text-blue-600' :
             action === 'buy' ? 'stroke-green-400 text-green-600' :
             action === 'sell' ? 'stroke-red-400 text-red-600' :
             'stroke-purple-500 text-purple-700';
    }
  };

  const colors = getColors();
  const progress = isActive ? confirmation.progress * 100 : 0;
  
  // Dynamic tooltip text
  const getTooltipText = () => {
    return `Confirmation Timer: A risk management safety mechanism that introduces a deliberate delay before executing trades. This prevents impulsive decisions based on brief market fluctuations and allows time to verify that trading signals remain consistent before committing capital.`;
  };
  
  return (
    <div className={`flex items-center space-x-3 ${className}`} data-testid="confirmation-timer">
      {/* Circle */}
      <Tooltip content={getTooltipText()}>
        <div className="relative flex items-center cursor-help">
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
            strokeDashoffset={125.66 - (progress / 100) * 125.66}
            className={`${colors} transition-all duration-1000`}
            strokeLinecap="round"
          />
        </svg>
        
        <div className="absolute inset-0 flex items-center justify-center">
          <div className="text-center">
            <div className="text-xs">
              {isActive ? '⏱️' : 
               action === 'suspended_cooldown' ? '🚫' :
               action === 'buy' ? '📈' : 
               action === 'sell' ? '📉' : '👁️'}
            </div>
            <div className={`text-xs font-bold ${colors}`}>
              {isActive ? `${Math.floor(confirmation.time_remaining_seconds / 60)}:${String(confirmation.time_remaining_seconds % 60).padStart(2, '0')}` : 
               action === 'suspended_cooldown' ? 'BLOCKED' :
               action === 'none' ? 'WAIT' : 'READY'}
            </div>
          </div>
        </div>
      </div>
      </Tooltip>

      <div className="flex-1 min-w-0">
        <div className={`text-sm font-medium ${colors}`}>
          {isActive ? 'Confirmation Timer' : 
           action === 'suspended_cooldown' ? 'Execution Status' :
           action === 'none' ? 'Monitoring' : 'Ready to Trade'}
        </div>
        <div className="text-xs text-gray-500">
          {isActive ? `${progress.toFixed(0)}% complete` : 
           action === 'suspended_cooldown' ? 'Cannot execute' :
           action === 'none' ? 'Waiting for signal' : 'Can execute now'}
        </div>
      </div>
    </div>
  );
};

export default CircularConfirmationTimer;
