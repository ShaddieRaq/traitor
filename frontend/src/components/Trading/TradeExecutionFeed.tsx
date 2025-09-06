import React from 'react';
import { useTradeExecutionUpdates, TradeExecutionUpdate } from '../../hooks/useTradeExecutionUpdates';

const getStatusIcon = (status: string) => {
  switch (status) {
    case 'starting':
      return <span className="animate-pulse">🔄</span>;
    case 'placing_order':
      return <span className="animate-spin">⚡</span>;
    case 'order_placed':
      return <span className="text-blue-500">📋</span>;
    case 'recording':
      return <span className="animate-pulse">💾</span>;
    case 'completed':
      return <span className="text-green-500">✅</span>;
    case 'failed':
      return <span className="text-red-500">❌</span>;
    default:
      return <span>📊</span>;
  }
};

const getStatusColor = (status: string) => {
  switch (status) {
    case 'starting':
      return 'bg-blue-50 border-blue-200 text-blue-800';
    case 'placing_order':
      return 'bg-yellow-50 border-yellow-200 text-yellow-800 animate-pulse';
    case 'order_placed':
      return 'bg-purple-50 border-purple-200 text-purple-800';
    case 'recording':
      return 'bg-indigo-50 border-indigo-200 text-indigo-800';
    case 'completed':
      return 'bg-green-50 border-green-200 text-green-800';
    case 'failed':
      return 'bg-red-50 border-red-200 text-red-800';
    default:
      return 'bg-gray-50 border-gray-200 text-gray-800';
  }
};

interface TradeExecutionUpdateCardProps {
  update: TradeExecutionUpdate;
  isLatest: boolean;
}

const TradeExecutionUpdateCard: React.FC<TradeExecutionUpdateCardProps> = ({ update, isLatest }) => {
  const timestamp = new Date(update.timestamp).toLocaleTimeString();
  
  return (
    <div className={`border rounded-lg p-3 ${getStatusColor(update.status)} ${isLatest ? 'ring-2 ring-opacity-50' : ''}`}>
      <div className="flex items-center justify-between mb-2">
        <div className="flex items-center space-x-2">
          {getStatusIcon(update.status)}
          <span className="font-medium text-sm">
            Bot {update.bot_id} {update.bot_name && `(${update.bot_name})`}
          </span>
          {update.side && update.size_usd && (
            <span className="text-xs font-mono bg-white bg-opacity-50 px-2 py-1 rounded">
              {update.side} ${update.size_usd.toFixed(2)}
            </span>
          )}
        </div>
        <span className="text-xs opacity-75">{timestamp}</span>
      </div>
      
      <div className="text-sm mb-2">
        <span className="font-medium">{update.stage}:</span> {update.message}
      </div>

      {update.execution_details && (
        <div className="text-xs bg-white bg-opacity-50 rounded p-2 font-mono">
          <div className="flex justify-between">
            <span>{update.execution_details.side} ${update.execution_details.amount.toFixed(2)}</span>
            <span>@ ${update.execution_details.price.toFixed(2)}</span>
          </div>
          <div className="text-gray-600 mt-1">Order: {update.execution_details.order_id}</div>
        </div>
      )}

      {update.error && (
        <div className="text-xs bg-red-100 text-red-700 rounded p-2 mt-2">
          Error: {update.error}
        </div>
      )}
    </div>
  );
};

export const TradeExecutionFeed: React.FC = () => {
  const { updates, latestUpdate, isConnected, isExecuting, clearUpdates } = useTradeExecutionUpdates();

  if (!isConnected) {
    return (
      <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-4">
        <div className="flex items-center space-x-2">
          <span className="animate-pulse">🔄</span>
          <span className="text-yellow-800">Connecting to real-time updates...</span>
        </div>
      </div>
    );
  }

  if (updates.length === 0) {
    return (
      <div className="bg-green-50 border border-green-200 rounded-lg p-4">
        <div className="flex items-center space-x-2">
          <span>✅</span>
          <span className="text-green-800">Connected - Waiting for trade activity</span>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-4">
      {/* Connection Status & Controls */}
      <div className="flex items-center justify-between">
        <div className="flex items-center space-x-2">
          <span className="w-2 h-2 bg-green-500 rounded-full animate-pulse"></span>
          <span className="text-sm text-green-600">Live Updates Connected</span>
          {isExecuting && (
            <>
              <span className="text-gray-400">•</span>
              <span className="text-sm text-blue-600 font-medium animate-pulse">Trade Executing...</span>
            </>
          )}
        </div>
        {updates.length > 0 && (
          <button
            onClick={clearUpdates}
            className="text-xs text-gray-500 hover:text-gray-700 px-2 py-1 rounded border hover:bg-gray-50"
          >
            Clear ({updates.length})
          </button>
        )}
      </div>

      {/* Latest Update (Highlighted) */}
      {latestUpdate && (
        <div className="mb-4">
          <h4 className="text-sm font-medium text-gray-700 mb-2">Latest Update:</h4>
          <TradeExecutionUpdateCard update={latestUpdate} isLatest={true} />
        </div>
      )}

      {/* Recent Updates */}
      {updates.length > 1 && (
        <div>
          <h4 className="text-sm font-medium text-gray-700 mb-2">Recent Activity:</h4>
          <div className="space-y-2 max-h-96 overflow-y-auto">
            {updates.slice(1, 10).map((update, index) => (
              <TradeExecutionUpdateCard
                key={`${update.bot_id}-${update.timestamp}-${index}`}
                update={update}
                isLatest={false}
              />
            ))}
          </div>
        </div>
      )}
    </div>
  );
};
