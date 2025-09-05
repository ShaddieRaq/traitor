import React, { useState, useEffect } from 'react';

interface CooldownTimerProps {
  cooldownMinutes: number;
  className?: string;
}

const CooldownTimer: React.FC<CooldownTimerProps> = ({ cooldownMinutes, className = '' }) => {
  const [timeRemaining, setTimeRemaining] = useState(cooldownMinutes);

  useEffect(() => {
    setTimeRemaining(cooldownMinutes);
  }, [cooldownMinutes]);

  useEffect(() => {
    if (timeRemaining <= 0) return;

    const timer = setInterval(() => {
      setTimeRemaining((prev) => {
        const newTime = prev - (1/60); // Decrease by 1 second (1/60 of a minute)
        return newTime > 0 ? newTime : 0;
      });
    }, 1000);

    return () => clearInterval(timer);
  }, [timeRemaining]);

  if (cooldownMinutes <= 0) return null;

  const minutes = Math.floor(timeRemaining);
  const seconds = Math.floor((timeRemaining - minutes) * 60);
  const progress = Math.max(0, 100 - (timeRemaining / 15) * 100); // Assuming 15 min max cooldown

  return (
    <div className={`bg-blue-50 border border-blue-200 rounded-lg p-3 ${className}`}>
      <div className="flex items-center justify-between mb-2">
        <div className="flex items-center space-x-2">
          <span className="text-blue-600">❄️</span>
          <span className="text-sm font-medium text-blue-800">Trade Cooldown</span>
        </div>
        <div className="text-lg font-mono font-bold text-blue-900">
          {minutes}:{seconds.toString().padStart(2, '0')}
        </div>
      </div>
      
      {/* Progress Bar */}
      <div className="w-full bg-blue-200 rounded-full h-2 mb-2">
        <div 
          className="bg-blue-600 h-2 rounded-full transition-all duration-1000 ease-out"
          style={{ width: `${progress}%` }}
        ></div>
      </div>
      
      <div className="text-xs text-blue-600 text-center">
        Trading will resume when timer reaches 0:00
      </div>
    </div>
  );
};

export default CooldownTimer;
