import React from 'react';
import { useState } from 'react';
import { useQuery } from '@tanstack/react-query';

interface ErrorIndicatorProps {
  botId: number;
  botName: string;
  className?: string;
}

interface BotError {
  id: string;
  message: string;
  timestamp: string;
  type: 'signal_calculation' | 'market_data' | 'configuration' | 'trading_logic';
  bot_id: number;
  bot_name: string;
  resolved: boolean;
}

const ErrorIndicator: React.FC<ErrorIndicatorProps> = ({ botId, className = '' }) => {
  const [showDetails, setShowDetails] = useState(false);

  // Fetch errors for this specific bot
  const { data: errors = [] } = useQuery<BotError[]>({
    queryKey: ['system-errors', 'bot', botId],
    queryFn: async () => {
      const response = await fetch(`/api/v1/system-errors/bot/${botId}`);
      if (!response.ok) throw new Error('Failed to fetch bot errors');
      return response.json();
    },
    refetchInterval: 10000, // Check for errors every 10 seconds
  });

  // Only show unresolved errors
  const activeErrors = errors.filter(error => !error.resolved);
  
  if (activeErrors.length === 0) return null;

  const primaryError = activeErrors[0]; // Show most recent error

  const getErrorIcon = (type: string) => {
    switch (type) {
      case 'signal_calculation': return '📊';
      case 'market_data': return '📡';
      case 'configuration': return '⚙️';
      case 'trading_logic': return '🤖';
      default: return '⚠️';
    }
  };

  const getErrorColor = (type: string) => {
    switch (type) {
      case 'signal_calculation': return 'bg-orange-100 text-orange-700 border-orange-200';
      case 'market_data': return 'bg-red-100 text-red-700 border-red-200';
      case 'configuration': return 'bg-purple-100 text-purple-700 border-purple-200';
      case 'trading_logic': return 'bg-yellow-100 text-yellow-700 border-yellow-200';
      default: return 'bg-gray-100 text-gray-700 border-gray-200';
    }
  };

  return (
    <div className={`${className}`}>
      <div 
        className={`inline-flex items-center px-2 py-1 rounded text-xs font-medium border cursor-pointer ${getErrorColor(primaryError.type)}`}
        onClick={() => setShowDetails(!showDetails)}
      >
        <span className="mr-1">{getErrorIcon(primaryError.type)}</span>
        Code Error
        {activeErrors.length > 1 && <span className="ml-1 text-xs">({activeErrors.length})</span>}
        <span className="ml-1">{showDetails ? '▼' : '▶'}</span>
      </div>
      
      {showDetails && (
        <div className={`mt-2 p-3 rounded-lg border ${getErrorColor(primaryError.type)} bg-opacity-50`}>
          <div className="text-xs font-medium mb-1">
            {primaryError.type.replace('_', ' ').toUpperCase()} ERROR
          </div>
          <div className="text-xs mb-2">{primaryError.message}</div>
          <div className="text-xs opacity-75">
            {new Date(primaryError.timestamp).toLocaleString()}
          </div>
          {activeErrors.length > 1 && (
            <div className="text-xs mt-2 pt-2 border-t border-gray-300">
              +{activeErrors.length - 1} more error{activeErrors.length > 2 ? 's' : ''}
            </div>
          )}
        </div>
      )}
    </div>
  );
};

export default ErrorIndicator;
