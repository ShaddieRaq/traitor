import React, { useState } from 'react';
import { useQuery } from '@tanstack/react-query';

// API types
interface TradingParameters {
  signal_quality: {
    min_confidence_threshold: number;
    description: string;
    impact: string;
  };
  trading_thresholds: {
    default_buy_threshold: number;
    default_sell_threshold: number;
    description: string;
    impact: string;
  };
  regime_adaptive_thresholds: {
    [regime: string]: { buy: number; sell: number };
    description: string;
    impact: string;
  };
  balance_requirements: {
    description: string;
    buy_trades: string;
    sell_trades: string;
    impact: string;
  };
}

interface BlockingSummary {
  total_bots: number;
  bots_with_strong_signals: number;
  blocking_reasons: {
    low_confidence: number;
    insufficient_balance: number;
    weak_signals: number;
    awaiting_confirmation: number;
    system_errors: number;
  };
  examples: Array<{
    bot_id: number;
    pair: string;
    score: number;
    confidence: number;
    action: string;
    primary_blocking_reason: string;
  }>;
}

// API functions
const fetchTradingParameters = async (): Promise<TradingParameters> => {
  const response = await fetch('/api/v1/system-diagnostics/trading-parameters');
  if (!response.ok) throw new Error('Failed to fetch trading parameters');
  return response.json();
};

const fetchBlockingSummary = async (): Promise<BlockingSummary> => {
  const response = await fetch('/api/v1/system-diagnostics/trading-blocks-summary');
  if (!response.ok) throw new Error('Failed to fetch blocking summary');
  return response.json();
};

const SystemDiagnosticsCard: React.FC = () => {
  const [activeTab, setActiveTab] = useState<'parameters' | 'blocking'>('parameters');

  const { data: parameters, isLoading: loadingParams } = useQuery({
    queryKey: ['trading-parameters'],
    queryFn: fetchTradingParameters,
    refetchInterval: 60000,
  });

  const { data: blockingSummary, isLoading: loadingBlocking } = useQuery({
    queryKey: ['blocking-summary'],
    queryFn: fetchBlockingSummary,
    refetchInterval: 30000,
  });

  if (loadingParams || loadingBlocking) {
    return (
      <div className="bg-white rounded-lg shadow-md p-6">
        <div className="animate-pulse">
          <div className="h-4 bg-gray-200 rounded w-1/3 mb-4"></div>
          <div className="space-y-3">
            <div className="h-3 bg-gray-200 rounded w-full"></div>
            <div className="h-3 bg-gray-200 rounded w-2/3"></div>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="bg-white rounded-lg shadow-md p-6">
      <div className="flex items-center justify-between mb-6">
        <div>
          <h3 className="text-lg font-semibold text-gray-900">
            🔧 System Diagnostics
          </h3>
          <p className="text-sm text-gray-600">
            Critical parameters affecting bot trading decisions
          </p>
        </div>
      </div>

      <div className="flex space-x-1 mb-6">
        <button
          onClick={() => setActiveTab('parameters')}
          className={`px-4 py-2 text-sm font-medium rounded-lg transition-colors ${
            activeTab === 'parameters'
              ? 'bg-blue-100 text-blue-700'
              : 'text-gray-500 hover:text-gray-700'
          }`}
        >
          Trading Parameters
        </button>
        <button
          onClick={() => setActiveTab('blocking')}
          className={`px-4 py-2 text-sm font-medium rounded-lg transition-colors ${
            activeTab === 'blocking'
              ? 'bg-blue-100 text-blue-700'
              : 'text-gray-500 hover:text-gray-700'
          }`}
        >
          Trading Blocks
        </button>
      </div>

      {activeTab === 'parameters' && parameters && (
        <div className="space-y-6">
          <div className="border-l-4 border-red-500 pl-4">
            <h4 className="font-semibold text-red-700 mb-2">
              🚫 Signal Confidence Filter
            </h4>
            <div className="text-sm space-y-1">
              <p><strong>Minimum Required:</strong> {(parameters.signal_quality.min_confidence_threshold * 100).toFixed(0)}%</p>
              <p className="text-gray-600">{parameters.signal_quality.description}</p>
              <p className="text-red-600 font-medium">{parameters.signal_quality.impact}</p>
            </div>
          </div>

          <div className="border-l-4 border-blue-500 pl-4">
            <h4 className="font-semibold text-blue-700 mb-2">
              📊 Signal Score Thresholds
            </h4>
            <div className="text-sm space-y-1">
              <p><strong>Buy Signal:</strong> ≤ {parameters.trading_thresholds.default_buy_threshold}</p>
              <p><strong>Sell Signal:</strong> ≥ {parameters.trading_thresholds.default_sell_threshold}</p>
              <p className="text-gray-600">{parameters.trading_thresholds.description}</p>
              <p className="text-blue-600 font-medium">{parameters.trading_thresholds.impact}</p>
            </div>
          </div>

          <div className="border-l-4 border-green-500 pl-4">
            <h4 className="font-semibold text-green-700 mb-2">
              💰 Balance Requirements
            </h4>
            <div className="text-sm space-y-1">
              <p><strong>Buy Trades:</strong> {parameters.balance_requirements.buy_trades}</p>
              <p><strong>Sell Trades:</strong> {parameters.balance_requirements.sell_trades}</p>
              <p className="text-green-600 font-medium">{parameters.balance_requirements.impact}</p>
            </div>
          </div>
        </div>
      )}

      {activeTab === 'blocking' && blockingSummary && (
        <div className="space-y-6">
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <div className="bg-blue-50 p-3 rounded-lg">
              <p className="text-2xl font-bold text-blue-700">{blockingSummary.total_bots}</p>
              <p className="text-sm text-blue-600">Total Bots</p>
            </div>
            <div className="bg-green-50 p-3 rounded-lg">
              <p className="text-2xl font-bold text-green-700">{blockingSummary.bots_with_strong_signals}</p>
              <p className="text-sm text-green-600">Strong Signals</p>
            </div>
            <div className="bg-red-50 p-3 rounded-lg">
              <p className="text-2xl font-bold text-red-700">{blockingSummary.blocking_reasons.low_confidence}</p>
              <p className="text-sm text-red-600">Low Confidence</p>
            </div>
            <div className="bg-yellow-50 p-3 rounded-lg">
              <p className="text-2xl font-bold text-yellow-700">{blockingSummary.blocking_reasons.insufficient_balance}</p>
              <p className="text-sm text-yellow-600">Insufficient Balance</p>
            </div>
          </div>

          <div>
            <h4 className="font-semibold text-gray-800 mb-3">🚫 Primary Blocking Factors</h4>
            <div className="space-y-2">
              {Object.entries(blockingSummary.blocking_reasons).map(([reason, count]) => (
                <div key={reason} className="flex justify-between items-center py-2 px-3 bg-gray-50 rounded">
                  <span className="capitalize font-medium">{reason.replace('_', ' ')}</span>
                  <span className={`px-2 py-1 rounded text-sm font-bold ${
                    count > 0 ? 'bg-red-100 text-red-700' : 'bg-green-100 text-green-700'
                  }`}>
                    {count} bots
                  </span>
                </div>
              ))}
            </div>
          </div>

          {blockingSummary.examples.length > 0 && (
            <div>
              <h4 className="font-semibold text-gray-800 mb-3">📋 Example Blocked Bots</h4>
              <div className="space-y-2">
                {blockingSummary.examples.map((example) => (
                  <div key={example.bot_id} className="p-3 bg-gray-50 rounded-lg">
                    <div className="flex justify-between items-start">
                      <div>
                        <p className="font-medium">{example.pair}</p>
                        <p className="text-sm text-gray-600">
                          Score: {example.score.toFixed(3)} | 
                          Confidence: {(example.confidence * 100).toFixed(1)}%
                        </p>
                      </div>
                      <span className="px-2 py-1 bg-red-100 text-red-700 rounded text-xs font-medium">
                        {example.primary_blocking_reason.replace('_', ' ')}
                      </span>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
};

export default SystemDiagnosticsCard;