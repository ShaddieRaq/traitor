import React, { useState } from 'react';
import { ChevronDown, ChevronUp, Activity, TrendingUp, Clock, DollarSign } from 'lucide-react';
import PerformanceTrend from './PerformanceTrend';
import { useLivePortfolio } from '../../hooks/useLivePortfolio';

export interface ExpandableBotCardProps {
  bot: any;
  className?: string;
}

/**
 * Expandable bot card with progressive disclosure
 * Shows basic info collapsed, detailed metrics when expanded
 */
export const ExpandableBotCard: React.FC<ExpandableBotCardProps> = ({ 
  bot, 
  className = '' 
}) => {
  const [isExpanded, setIsExpanded] = useState(false);
  
  // Get live portfolio data to show real position values
  const { data: livePortfolioData } = useLivePortfolio();
  
  // Helper function to get live position value for this bot's currency
  const getLivePositionValue = () => {
    if (!livePortfolioData?.holdings) return 0;
    
    // Extract currency from pair (e.g., "BTC-USD" -> "BTC")
    const currency = bot.pair?.split('-')[0];
    if (!currency) return 0;
    
    const holding = livePortfolioData.holdings.find(h => h.currency === currency);
    return holding?.value_usd || 0;
  };
  
  // Helper function to get live balance for this bot's currency  
  const getLiveBalance = () => {
    if (!livePortfolioData?.holdings) return 0;
    
    const currency = bot.pair?.split('-')[0];
    if (!currency) return 0;
    
    const holding = livePortfolioData.holdings.find(h => h.currency === currency);
    return holding?.balance || 0;
  };

  const getTemperatureColor = () => {
    switch (bot.temperature) {
      case 'HOT': return 'border-red-200 bg-red-50';
      case 'WARM': return 'border-orange-200 bg-orange-50';
      case 'COOL': return 'border-blue-200 bg-blue-50';
      default: return 'border-gray-200 bg-gray-50';
    }
  };

  const getTemperatureIcon = () => {
    switch (bot.temperature) {
      case 'HOT': return '🔥';
      case 'WARM': return '🌡️';
      case 'COOL': return '❄️';
      default: return '🧊';
    }
  };

  const getActionColor = () => {
    if (bot.current_combined_score > 0.1) return 'text-green-600';
    if (bot.current_combined_score < -0.1) return 'text-red-600';
    return 'text-gray-600';
  };

  const getActionText = () => {
    if (bot.current_combined_score > 0.1) return 'BUY';
    if (bot.current_combined_score < -0.1) return 'SELL';
    return 'HOLD';
  };

  const generatePerformanceHistory = () => {
    const points = 15;
    const liveValue = getLivePositionValue();
    const baseValue = liveValue > 0 ? liveValue : 100; // Use live value or small default
    return Array.from({ length: points }, (_, i) => {
      // Use bot.id as seed for stable data instead of random
      const seed = (bot.id * 17 + i) % 100;
      const trend = baseValue * (1 + (seed / 100 - 0.5) * 0.05); // Much smaller, stable variation
      return Math.max(0, trend);
    });
  };

  // Calculate trading intent based on current signal - don't use potentially stale bot.trading_intent
  const tradingIntent = {
    next_action: getActionText().toLowerCase(),
    signal_strength: Math.abs(bot.current_combined_score || 0),
    confidence: Math.abs(bot.current_combined_score || 0) * 0.8, // Confidence based on signal strength
    distance_to_threshold: bot.distance_to_signal || 0.0
  };

  const mockTradeReadiness = bot.trade_readiness || {
    status: bot.status === 'ACTIVE' ? 'ready' : 'paused',
    can_trade: bot.status === 'ACTIVE',
    blocking_reason: bot.status === 'ACTIVE' ? null : 'Bot paused',
    cooldown_remaining_minutes: 15 // Fixed value instead of random
  };

  return (
    <div className={`
      ${getTemperatureColor()}
      rounded-lg border-2 transition-all duration-300
      ${isExpanded ? 'shadow-lg' : 'shadow-sm hover:shadow-md'}
      ${className}
    `}>
      {/* Collapsed Header - Always Visible */}
      <div 
        className="p-4 cursor-pointer"
        onClick={() => setIsExpanded(!isExpanded)}
      >
        <div className="flex items-center justify-between">
          {/* Left: Bot Info */}
          <div className="flex items-center space-x-3">
            <div>
              <div className="font-semibold text-gray-900">{bot.pair}</div>
              <div className="text-sm text-gray-600">{bot.name}</div>
            </div>
            <div className="flex items-center space-x-2">
              <span className="text-xl">{getTemperatureIcon()}</span>
              <span className={`text-xs px-2 py-1 rounded-full ${
                bot.status === 'ACTIVE' ? 'bg-green-100 text-green-800' : 'bg-gray-100 text-gray-600'
              }`}>
                {bot.status}
              </span>
            </div>
          </div>

          {/* Center: Action & Score */}
          <div className="text-center">
            <div className={`text-lg font-bold ${getActionColor()}`}>
              {getActionText()}
            </div>
            <div className="text-xs text-gray-600">
              {bot.current_combined_score.toFixed(3)}
            </div>
          </div>

          {/* Right: Expand Button */}
          <div className="flex items-center space-x-2">
            {!isExpanded && (
              <div className="text-xs text-gray-500">
                Click for details
              </div>
            )}
            {isExpanded ? (
              <ChevronUp className="h-5 w-5 text-gray-400" />
            ) : (
              <ChevronDown className="h-5 w-5 text-gray-400" />
            )}
          </div>
        </div>
      </div>

      {/* Expanded Content */}
      {isExpanded && (
        <div className="border-t border-gray-200 bg-white bg-opacity-50">
          {/* Trading Intent Section */}
          <div className="p-4 border-b border-gray-200">
            <h4 className="text-sm font-semibold text-gray-900 mb-3 flex items-center">
              <Activity className="h-4 w-4 mr-2" />
              Trading Intent
            </h4>
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
              <div>
                <div className="text-xs text-gray-600">Next Action</div>
                <div className={`font-semibold ${
                  tradingIntent.next_action === 'buy' ? 'text-green-600' :
                  tradingIntent.next_action === 'sell' ? 'text-red-600' : 'text-gray-600'
                }`}>
                  {tradingIntent.next_action.toUpperCase()}
                </div>
              </div>
              <div>
                <div className="text-xs text-gray-600">Signal Strength</div>
                <div className="font-semibold">
                  {(tradingIntent.signal_strength * 100).toFixed(1)}%
                </div>
              </div>
              <div>
                <div className="text-xs text-gray-600">Confidence</div>
                <div className="font-semibold">
                  {(tradingIntent.confidence * 100).toFixed(1)}%
                </div>
              </div>
              <div>
                <div className="text-xs text-gray-600">Distance to Threshold</div>
                <div className="font-semibold">
                  {tradingIntent.distance_to_threshold.toFixed(3)}
                </div>
              </div>
            </div>
          </div>

          {/* Signal Summary - Much Clearer Than Oscillating Chart */}
          <div className="p-4 border-b border-gray-200">
            <h4 className="text-sm font-semibold text-gray-900 mb-3 flex items-center">
              <TrendingUp className="h-4 w-4 mr-2" />
              Current Signal Analysis
            </h4>
            <div className="bg-gray-50 rounded-lg p-4">
              <div className="flex items-center justify-between mb-2">
                <span className="text-sm text-gray-600">Signal Strength:</span>
                <span className={`font-bold text-lg ${getActionColor()}`}>
                  {bot.current_combined_score.toFixed(3)}
                </span>
              </div>
              <div className="flex items-center justify-between mb-2">
                <span className="text-sm text-gray-600">Recommendation:</span>
                <span className={`font-bold ${getActionColor()}`}>
                  {getActionText()}
                </span>
              </div>
              <div className="text-xs text-gray-500 mt-2 leading-relaxed">
                Signal ranges from -1.0 (strong sell) to +1.0 (strong buy). 
                Values above 0.1 suggest buying, below -0.1 suggest selling.
              </div>
            </div>
          </div>

          {/* Performance Metrics */}
          <div className="p-4 border-b border-gray-200">
            <h4 className="text-sm font-semibold text-gray-900 mb-3 flex items-center">
              <DollarSign className="h-4 w-4 mr-2" />
              Performance Metrics
            </h4>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                            <PerformanceTrend
                title="Position Value"
                currentValue={getLivePositionValue()}
                change={getLivePositionValue() * 0.05} // Mock 5% change
                format="currency"
                historicalData={generatePerformanceHistory()}
                size="lg"
                showChart={true}
              />
              <PerformanceTrend
                title="Position Size"
                currentValue={bot.current_position_size || 0}
                format="number"
                size="sm"
                showChart={false}
              />
            </div>
          </div>

          {/* Trade Readiness */}
          <div className="p-4 border-b border-gray-200">
            <h4 className="text-sm font-semibold text-gray-900 mb-3 flex items-center">
              <Clock className="h-4 w-4 mr-2" />
              Trade Readiness
            </h4>
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
              <div>
                <div className="text-xs text-gray-600">Live Balance</div>
                <div className="font-semibold text-blue-600">
                  {getLiveBalance().toFixed(4)} {bot.pair?.split('-')[0]}
                </div>
              </div>
              <div>
                <div className="text-xs text-gray-600">Live Value</div>
                <div className="font-semibold text-green-600">
                  ${getLivePositionValue().toFixed(2)}
                </div>
              </div>
              <div>
                <div className="text-xs text-gray-600">Status</div>
                <div className={`font-semibold ${
                  mockTradeReadiness.can_trade ? 'text-green-600' : 'text-yellow-600'
                }`}>
                  {mockTradeReadiness.status.toUpperCase()}
                </div>
              </div>
              <div>
                <div className="text-xs text-gray-600">Temperature</div>
                <div className="font-semibold">
                  {bot.temperature}
                </div>
              </div>
            </div>
            {mockTradeReadiness.blocking_reason && (
              <div className="mt-2 text-xs text-red-600 bg-red-50 p-2 rounded">
                ⚠️ {mockTradeReadiness.blocking_reason}
              </div>
            )}
          </div>

          {/* Action Buttons */}
          <div className="p-4">
            <div className="flex gap-2">
              <button className="flex-1 bg-blue-500 hover:bg-blue-600 text-white py-2 px-3 rounded-lg text-sm font-medium transition-colors">
                📊 View Full Analytics
              </button>
              <button className="flex-1 bg-gray-500 hover:bg-gray-600 text-white py-2 px-3 rounded-lg text-sm font-medium transition-colors">
                ⚙️ Configure Bot
              </button>
              <button className="flex-1 bg-green-500 hover:bg-green-600 text-white py-2 px-3 rounded-lg text-sm font-medium transition-colors">
                ⚡ Quick Trade
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default ExpandableBotCard;
