import React from 'react';
import { TradeExecutionUpdate } from '../../hooks/useTradeExecutionUpdates';

interface TradeProgressIndicatorProps {
  updates: TradeExecutionUpdate[];
  isExecuting: boolean;
}

const tradeStages = [
  { key: 'starting', label: 'Starting', description: 'Initializing trade' },
  { key: 'placing_order', label: 'Placing Order', description: 'Submitting to exchange' },
  { key: 'order_placed', label: 'Order Placed', description: 'Waiting for fill' },
  { key: 'recording', label: 'Recording', description: 'Saving trade data' },
  { key: 'completed', label: 'Completed', description: 'Trade finished' }
];

const getStageStatus = (stageKey: string, updates: TradeExecutionUpdate[]) => {
  const latestUpdate = updates[0];
  if (!latestUpdate) return 'pending';

  const stageIndex = tradeStages.findIndex(stage => stage.key === stageKey);
  const currentStageIndex = tradeStages.findIndex(stage => stage.key === latestUpdate.status);

  if (latestUpdate.status === 'failed') {
    return stageIndex <= currentStageIndex ? 'error' : 'pending';
  }

  if (stageIndex < currentStageIndex) return 'completed';
  if (stageIndex === currentStageIndex) return 'active';
  return 'pending';
};

const StageIndicator: React.FC<{
  stage: typeof tradeStages[0];
  status: 'pending' | 'active' | 'completed' | 'error';
  isLast: boolean;
}> = ({ stage, status, isLast }) => {
  const getIndicatorStyles = () => {
    switch (status) {
      case 'completed':
        return 'bg-green-500 text-white border-green-500';
      case 'active':
        return 'bg-blue-500 text-white border-blue-500 animate-pulse';
      case 'error':
        return 'bg-red-500 text-white border-red-500';
      default:
        return 'bg-gray-200 text-gray-500 border-gray-300';
    }
  };

  const getLineStyles = () => {
    switch (status) {
      case 'completed':
        return 'bg-green-500';
      case 'active':
        return 'bg-gradient-to-r from-green-500 to-blue-500';
      case 'error':
        return 'bg-red-500';
      default:
        return 'bg-gray-300';
    }
  };

  return (
    <div className="flex items-center">
      <div className="flex flex-col items-center">
        <div className={`w-8 h-8 rounded-full border-2 flex items-center justify-center text-sm font-medium ${getIndicatorStyles()}`}>
          {status === 'completed' ? '✓' : status === 'error' ? '✗' : tradeStages.findIndex(s => s.key === stage.key) + 1}
        </div>
        <div className="text-center mt-2">
          <div className="text-xs font-medium text-gray-700">{stage.label}</div>
          <div className="text-xs text-gray-500">{stage.description}</div>
        </div>
      </div>
      
      {!isLast && (
        <div className={`w-16 h-1 mx-2 ${getLineStyles()} transition-all duration-300`}></div>
      )}
    </div>
  );
};

export const TradeProgressIndicator: React.FC<TradeProgressIndicatorProps> = ({ updates, isExecuting }) => {
  const latestUpdate = updates[0];

  if (!isExecuting && updates.length === 0) {
    return null;
  }

  return (
    <div className="bg-white rounded-lg border border-gray-200 p-4">
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-sm font-medium text-gray-900">Trade Execution Progress</h3>
        {latestUpdate && (
          <div className="text-xs text-gray-500">
            Bot {latestUpdate.bot_id} • {new Date(latestUpdate.timestamp).toLocaleTimeString()}
          </div>
        )}
      </div>

      <div className="flex items-center justify-between">
        {tradeStages.map((stage, index) => (
          <StageIndicator
            key={stage.key}
            stage={stage}
            status={getStageStatus(stage.key, updates)}
            isLast={index === tradeStages.length - 1}
          />
        ))}
      </div>

      {latestUpdate && (
        <div className="mt-4 p-3 bg-gray-50 rounded">
          <div className="text-sm">
            <span className="font-medium">{latestUpdate.stage}:</span> {latestUpdate.message}
          </div>
          {latestUpdate.execution_details && (
            <div className="text-xs text-gray-600 mt-1 font-mono">
              {latestUpdate.execution_details.side} ${latestUpdate.execution_details.amount.toFixed(2)} @ ${latestUpdate.execution_details.price.toFixed(2)}
            </div>
          )}
          {latestUpdate.error && (
            <div className="text-xs text-red-600 mt-1 font-medium">
              Error: {latestUpdate.error}
            </div>
          )}
        </div>
      )}
    </div>
  );
};
