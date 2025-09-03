import React from 'react';

interface BotEvaluationStatusProps {
  lastEvaluated?: string;
  isEvaluating?: boolean;
  evaluationError?: string;
}

export const BotEvaluationStatus: React.FC<BotEvaluationStatusProps> = ({
  lastEvaluated,
  isEvaluating = false,
  evaluationError
}) => {
  if (evaluationError) {
    return (
      <div className="flex items-center space-x-1" title={`Evaluation error: ${evaluationError}`}>
        <div className="w-2 h-2 bg-red-400 rounded-full"></div>
        <span className="text-xs text-red-600">Error</span>
      </div>
    );
  }

  if (isEvaluating) {
    return (
      <div className="flex items-center space-x-1" title="Bot evaluation in progress">
        <div className="w-2 h-2 bg-blue-400 rounded-full animate-pulse"></div>
        <span className="text-xs text-blue-600">Evaluating...</span>
      </div>
    );
  }

  if (lastEvaluated) {
    const lastEvaluatedTime = new Date(lastEvaluated);
    const now = new Date();
    const secondsAgo = Math.floor((now.getTime() - lastEvaluatedTime.getTime()) / 1000);
    
    let color = 'bg-green-400';
    
    if (secondsAgo > 60) {
      color = 'bg-yellow-400';
    } else if (secondsAgo > 300) {
      color = 'bg-red-400';
    }

    const formatTimeAgo = (seconds: number): string => {
      if (seconds < 60) return `${seconds}s`;
      if (seconds < 3600) return `${Math.floor(seconds / 60)}m`;
      return `${Math.floor(seconds / 3600)}h`;
    };

    return (
      <div className="flex items-center space-x-1" title={`Last evaluated ${formatTimeAgo(secondsAgo)} ago`}>
        <div className={`w-2 h-2 ${color} rounded-full`}></div>
        <span className="text-xs text-gray-500">{formatTimeAgo(secondsAgo)}</span>
      </div>
    );
  }

  return (
    <div className="flex items-center space-x-1" title="No evaluation data">
      <div className="w-2 h-2 bg-gray-400 rounded-full"></div>
      <span className="text-xs text-gray-500">Unknown</span>
    </div>
  );
};

interface TemperatureChangeIndicatorProps {
  currentTemperature: string;
  previousTemperature?: string;
  showChangeAnimation?: boolean;
}

export const TemperatureChangeIndicator: React.FC<TemperatureChangeIndicatorProps> = ({
  currentTemperature,
  previousTemperature,
  showChangeAnimation = true
}) => {
  const hasChanged = previousTemperature && previousTemperature !== currentTemperature;
  
  const getTemperatureEmoji = (temp: string) => {
    switch (temp) {
      case 'HOT': return '🔥';
      case 'WARM': return '🌡️';
      case 'COOL': return '❄️';
      default: return '🧊';
    }
  };

  const getTemperatureChangeDirection = () => {
    if (!previousTemperature) return null;
    
    const levels = ['FROZEN', 'COOL', 'WARM', 'HOT'];
    const currentLevel = levels.indexOf(currentTemperature);
    const previousLevel = levels.indexOf(previousTemperature);
    
    if (currentLevel > previousLevel) return '↗️'; // Heating up
    if (currentLevel < previousLevel) return '↘️'; // Cooling down
    return null;
  };

  const changeDirection = getTemperatureChangeDirection();

  return (
    <div className="flex items-center space-x-1">
      <span className={`text-2xl ${hasChanged && showChangeAnimation ? 'animate-pulse' : ''}`}>
        {getTemperatureEmoji(currentTemperature)}
      </span>
      {changeDirection && showChangeAnimation && (
        <span className="text-sm animate-bounce" title={`Temperature changed from ${previousTemperature} to ${currentTemperature}`}>
          {changeDirection}
        </span>
      )}
    </div>
  );
};
