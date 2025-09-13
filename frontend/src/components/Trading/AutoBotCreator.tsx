import React, { useState } from 'react';
import { useMutation, useQueryClient } from '@tanstack/react-query';
import api from '../../lib/api';

interface AutoBotCreationResult {
  success: boolean;
  total_candidates_analyzed: number;
  qualified_candidates: number;
  bots_created: number;
  new_bots: Array<{
    bot_id: number;
    bot_name: string;
    analysis: {
      product_id: string;
      total_score: number;
      recommendation: string;
    };
  }>;
  threshold_used: number;
}

interface AutoBotCreatorProps {
  className?: string;
}

export const AutoBotCreator: React.FC<AutoBotCreatorProps> = ({ className = '' }) => {
  const [maxBots, setMaxBots] = useState(2);
  const [minScore, setMinScore] = useState(16.0);
  const [isExpanded, setIsExpanded] = useState(false);
  
  const queryClient = useQueryClient();

  const autoCreateMutation = useMutation({
    mutationFn: async ({ maxBots, minScore }: { maxBots: number; minScore: number }) => {
      const response = await api.post(`/market-analysis/scan-and-create?max_bots=${maxBots}&min_score=${minScore}`);
      return response.data as AutoBotCreationResult;
    },
    onSuccess: () => {
      // Refresh bots data
      queryClient.invalidateQueries({ queryKey: ['bots'] });
      queryClient.invalidateQueries({ queryKey: ['enhanced-bots-status'] });
    },
  });

  const handleAutoCreate = () => {
    autoCreateMutation.mutate({ maxBots, minScore });
  };

  const getScoreColor = (score: number) => {
    if (score >= 20) return 'text-green-600';
    if (score >= 16) return 'text-yellow-600';
    return 'text-red-600';
  };

  const getScoreLabel = (threshold: number) => {
    if (threshold >= 20) return 'Exceptional Only';
    if (threshold >= 18) return 'High Quality';
    if (threshold >= 16) return 'Good Candidates';
    return 'Any Opportunity';
  };

  return (
    <div className={`bg-white rounded-lg border border-gray-200 shadow-sm ${className}`}>
      <div className="p-4">
        {/* Header with toggle */}
        <div className="flex items-center justify-between mb-4">
          <div className="flex items-center space-x-2">
            <span className="text-lg">🤖</span>
            <h3 className="text-lg font-semibold text-gray-900">Auto Bot Creator</h3>
            <span className="text-xs px-2 py-1 bg-blue-100 text-blue-700 rounded">BETA</span>
          </div>
          <button
            onClick={() => setIsExpanded(!isExpanded)}
            className="text-gray-500 hover:text-gray-700"
          >
            {isExpanded ? '▼' : '▶'}
          </button>
        </div>

        {/* Quick Action Button */}
        {!isExpanded && (
          <div className="flex items-center justify-between">
            <p className="text-sm text-gray-600">
              Scan market for opportunities and auto-create trading bots
            </p>
            <button
              onClick={handleAutoCreate}
              disabled={autoCreateMutation.isPending}
              className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed text-sm font-medium"
            >
              {autoCreateMutation.isPending ? 'Scanning...' : 'Quick Scan'}
            </button>
          </div>
        )}

        {/* Expanded Controls */}
        {isExpanded && (
          <div className="space-y-4">
            <p className="text-sm text-gray-600">
              Automatically scan the entire Coinbase market and create bots for the best trading opportunities.
            </p>

            {/* Controls */}
            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Max New Bots
                </label>
                <select
                  value={maxBots}
                  onChange={(e) => setMaxBots(Number(e.target.value))}
                  className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm"
                >
                  <option value={1}>1 Bot</option>
                  <option value={2}>2 Bots</option>
                  <option value={3}>3 Bots</option>
                  <option value={5}>5 Bots</option>
                </select>
                <div className="mt-1 text-xs text-green-600 font-medium">
                  Trade Size: $25 per bot
                </div>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Quality Threshold
                </label>
                <div className="space-y-1">
                  <input
                    type="range"
                    min="12"
                    max="22"
                    step="0.5"
                    value={minScore}
                    onChange={(e) => setMinScore(Number(e.target.value))}
                    className="w-full"
                  />
                  <div className="flex justify-between text-xs text-gray-500">
                    <span>Any (12)</span>
                    <span className={`font-medium ${getScoreColor(minScore)}`}>
                      {minScore} - {getScoreLabel(minScore)}
                    </span>
                    <span>Perfect (22)</span>
                  </div>
                </div>
              </div>
            </div>

            {/* Action Button */}
            <button
              onClick={handleAutoCreate}
              disabled={autoCreateMutation.isPending}
              className="w-full px-4 py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed font-medium"
            >
              {autoCreateMutation.isPending ? (
                <span className="flex items-center justify-center space-x-2">
                  <span className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin"></span>
                  <span>Scanning Market...</span>
                </span>
              ) : (
                `🔍 Scan & Create Up To ${maxBots} Bot${maxBots > 1 ? 's' : ''}`
              )}
            </button>
          </div>
        )}

        {/* Results Display */}
        {autoCreateMutation.data && (
          <div className="mt-4 p-3 border rounded-lg bg-gray-50">
            <div className="text-sm space-y-2">
              <div className="flex justify-between">
                <span className="text-gray-600">Market Scan Results:</span>
                <span className="font-medium">
                  {autoCreateMutation.data.total_candidates_analyzed} pairs analyzed
                </span>
              </div>
              
              <div className="flex justify-between">
                <span className="text-gray-600">Qualified Opportunities:</span>
                <span className="font-medium text-blue-600">
                  {autoCreateMutation.data.qualified_candidates} found
                </span>
              </div>

              <div className="flex justify-between">
                <span className="text-gray-600">New Bots Created:</span>
                <span className={`font-medium ${autoCreateMutation.data.bots_created > 0 ? 'text-green-600' : 'text-gray-600'}`}>
                  {autoCreateMutation.data.bots_created}
                </span>
              </div>

              {/* New Bots List */}
              {autoCreateMutation.data.new_bots.length > 0 && (
                <div className="mt-3 pt-3 border-t border-gray-200">
                  <p className="text-sm font-medium text-gray-700 mb-2">✅ New Bots Created:</p>
                  {autoCreateMutation.data.new_bots.map((bot, index) => (
                    <div key={index} className="flex items-center justify-between py-1">
                      <span className="text-sm font-medium text-gray-900">
                        {bot.analysis.product_id}
                      </span>
                      <div className="flex items-center space-x-2">
                        <span className={`text-xs px-2 py-1 rounded ${getScoreColor(bot.analysis.total_score)} bg-gray-100`}>
                          Score: {bot.analysis.total_score.toFixed(1)}
                        </span>
                        <span className="text-xs text-gray-500">
                          Bot #{bot.bot_id}
                        </span>
                      </div>
                    </div>
                  ))}
                  <p className="text-xs text-gray-500 mt-2">
                    💡 New bots start STOPPED for safety. Activate them manually when ready.
                  </p>
                </div>
              )}

              {autoCreateMutation.data.bots_created === 0 && (
                <div className="mt-3 pt-3 border-t border-gray-200">
                  <p className="text-sm text-gray-600">
                    💡 No new bots created. Try lowering the quality threshold or check if you already have bots for the top opportunities.
                  </p>
                </div>
              )}
            </div>
          </div>
        )}

        {/* Error Display */}
        {autoCreateMutation.error && (
          <div className="mt-4 p-3 border border-red-200 rounded-lg bg-red-50">
            <p className="text-sm text-red-600">
              ❌ Error: {autoCreateMutation.error instanceof Error ? autoCreateMutation.error.message : 'Unknown error'}
            </p>
          </div>
        )}
      </div>
    </div>
  );
};

export default AutoBotCreator;
