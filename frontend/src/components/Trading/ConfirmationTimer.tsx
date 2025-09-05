import React, { useEffect, useState } from 'react';
import { ConfirmationStatus } from '../../types';

interface ConfirmationTimerProps {
  confirmation: ConfirmationStatus;
  className?: string;
}

const ConfirmationTimer: React.FC<ConfirmationTimerProps> = ({ confirmation, className = '' }) => {
  const [timeRemaining, setTimeRemaining] = useState(confirmation.time_remaining_seconds);

  useEffect(() => {
    setTimeRemaining(confirmation.time_remaining_seconds);
  }, [confirmation.time_remaining_seconds]);

  useEffect(() => {
    if (!confirmation.is_active || timeRemaining <= 0) return;

    const interval = setInterval(() => {
      setTimeRemaining(prev => Math.max(0, prev - 1));
    }, 1000);

    return () => clearInterval(interval);
  }, [confirmation.is_active, timeRemaining]);

  if (!confirmation.is_active) {
    return null;
  }

  const minutes = Math.floor(timeRemaining / 60);
  const seconds = timeRemaining % 60;
  const progressPercentage = confirmation.progress * 100;

  const getActionColor = (action?: string) => {
    switch (action) {
      case 'buy': return 'text-green-600 bg-green-50';
      case 'sell': return 'text-red-600 bg-red-50';
      default: return 'text-blue-600 bg-blue-50';
    }
  };

  const getProgressColor = (progress: number) => {
    if (progress >= 1.0) return 'bg-green-500';
    if (progress >= 0.5) return 'bg-yellow-500';
    return 'bg-blue-500';
  };

  return (
    <div className={`${className}`}>
      <div className="flex items-center justify-between mb-2">
        <div className="flex items-center space-x-2">
          <div className="w-2 h-2 bg-yellow-400 rounded-full animate-pulse"></div>
          <span className="text-xs font-medium text-gray-700">
            Confirming {confirmation.action?.toUpperCase()}
          </span>
        </div>
        <div className={`text-xs px-2 py-1 rounded ${getActionColor(confirmation.action)}`}>
          {String(minutes).padStart(2, '0')}:{String(seconds).padStart(2, '0')}
        </div>
      </div>
      
      {/* Progress bar */}
      <div className="w-full bg-gray-200 rounded-full h-2">
        <div 
          className={`h-2 rounded-full transition-all duration-1000 ${getProgressColor(confirmation.progress)}`}
          style={{ width: `${progressPercentage}%` }}
        ></div>
      </div>
      
      {confirmation.progress >= 1.0 && (
        <div className="flex items-center mt-1">
          <div className="w-1 h-1 bg-green-400 rounded-full mr-1"></div>
          <span className="text-xs text-green-600 font-medium">
            Ready to trade!
          </span>
        </div>
      )}
    </div>
  );
};

export default ConfirmationTimer;
