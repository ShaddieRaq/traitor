import React from 'react';
import { TrendingUp, TrendingDown, Activity, Clock, Target, Shield, Zap, Brain, BarChart3 } from 'lucide-react';
import { useTrendAnalysis, getTrendDirection, getRegimeDisplay } from '../../hooks/useTrends';

// Sample 1: Compact Performance-Focused Card
export const CompactPerformanceCard: React.FC<{ bot: any, pnlData?: any }> = ({ bot, pnlData }) => {
  const botPnL = pnlData?.find((p: any) => p.product_id === bot.pair);
  const isProfit = (botPnL?.net_pnl_usd || 0) >= 0;
  const winRate = botPnL ? ((botPnL.sell_trades / botPnL.trade_count) * 100).toFixed(1) : '0';
  
  const getTemperatureColor = () => {
    switch (bot.temperature) {
      case 'HOT': return 'from-red-500 to-orange-500';
      case 'WARM': return 'from-orange-400 to-yellow-400';
      case 'COOL': return 'from-blue-400 to-cyan-400';
      case 'FROZEN': return 'from-gray-400 to-slate-400';
      default: return 'from-gray-300 to-gray-400';
    }
  };

  return (
    <div className="relative overflow-hidden bg-white rounded-xl shadow-lg border hover:shadow-xl transition-all duration-300">
      {/* Temperature Gradient Header */}
      <div className={`h-2 bg-gradient-to-r ${getTemperatureColor()}`}></div>
      
      <div className="p-4">
        {/* Header Row */}
        <div className="flex items-center justify-between mb-3">
          <div className="flex items-center space-x-2">
            <div className="text-lg font-bold text-gray-900">{bot.pair}</div>
            <span className="text-xl">{bot.temperature === 'HOT' ? '🔥' : bot.temperature === 'WARM' ? '🌡️' : bot.temperature === 'COOL' ? '❄️' : '🧊'}</span>
          </div>
          <div className={`text-right ${isProfit ? 'text-green-600' : 'text-red-600'}`}>
            <div className="text-lg font-bold">
              {isProfit ? '+' : '-'}${Math.abs(botPnL?.net_pnl_usd || 0).toFixed(2)}
            </div>
            <div className="text-xs opacity-75">{winRate}% Win Rate</div>
          </div>
        </div>

        {/* Signal Strength Visualization */}
        <div className="mb-3">
          <div className="flex items-center justify-between text-xs text-gray-600 mb-1">
            <span>Signal Strength</span>
            <div className="flex items-center space-x-2">
              <span className="font-mono">{(bot.current_combined_score || 0).toFixed(3)}</span>
              <span>({(Math.abs(bot.current_combined_score || 0) * 100).toFixed(1)}%)</span>
            </div>
          </div>
          <div className="h-2 bg-gray-200 rounded-full overflow-hidden">
            <div 
              className={`h-full rounded-full transition-all duration-500 ${
                (bot.current_combined_score || 0) > 0.05 ? 'bg-red-500' : 
                (bot.current_combined_score || 0) < -0.05 ? 'bg-green-500' : 'bg-yellow-500'
              }`}
              style={{ width: `${Math.min(Math.abs(bot.current_combined_score || 0) * 1000, 100)}%` }}
            ></div>
          </div>
        </div>

        {/* Confidence Meter with 20% Threshold Line */}
        <div className="mb-3">
          <div className="flex items-center justify-between text-xs text-gray-600 mb-1">
            <span>Signal Confidence</span>
            <div className="flex items-center space-x-2">
              <span className="font-mono">{((bot.signal_confidence || 0) * 100).toFixed(1)}%</span>
              {(bot.signal_confidence || 0) < 0.2 && (
                <span className="text-red-600 font-medium">{'< 20% req'}</span>
              )}
            </div>
          </div>
          <div className="relative h-2 bg-gray-200 rounded-full overflow-hidden">
            {/* Confidence Bar */}
            <div 
              className={`h-full transition-all duration-300 ${
                (bot.signal_confidence || 0) >= 0.2 ? 'bg-green-500' : 'bg-red-500'
              }`}
              style={{ width: `${Math.min((bot.signal_confidence || 0) * 100, 100)}%` }}
            ></div>
            {/* 20% Threshold Line */}
            <div 
              className="absolute top-0 w-0.5 h-full bg-gray-800 opacity-75"
              style={{ left: '20%' }}
              title="20% minimum required"
            ></div>
          </div>
        </div>

        {/* Balance Requirements Info - Only show when actually blocked */}
        {bot.trade_readiness?.status === 'blocked' && bot.trade_readiness?.blocking_reason?.includes('insufficient_balance') && (
          <div className="mb-3 p-2 bg-red-50 rounded-lg border border-red-200">
            <div className="flex items-center space-x-1 mb-1">
              <span className="text-xs font-medium text-red-700">💰 {bot.trade_readiness.blocking_reason.includes('USD') ? 'Need USD' : 'Need Crypto'}</span>
            </div>
            <div className="text-xs text-red-600">
              {bot.trade_readiness.blocking_reason.includes('USD') ? (
                <span>${bot.position_size_usd || 25} USD required</span>
              ) : (
                <span>Insufficient crypto holdings</span>
              )}
            </div>
          </div>
        )}

        {/* Risk Multiplier Info - Show position sizing adjustments */}
        {bot.position_sizing && bot.use_position_sizing && (
          <div className="mb-3 p-2 bg-blue-50 rounded-lg border border-blue-200">
            <div className="flex items-center justify-between mb-1">
              <span className="text-xs font-medium text-blue-700 flex items-center">
                <Shield className="h-3 w-3 mr-1" />
                Position Sizing
              </span>
              <span className="text-xs font-bold text-blue-800">
                {(bot.position_sizing.total_multiplier * 100).toFixed(0)}% of base
              </span>
            </div>
            <div className="text-xs text-blue-600">
              <div className="flex justify-between">
                <span>Base: ${bot.position_sizing.base_position_size}</span>
                <span>→ Actual: ${bot.position_sizing.final_position_size}</span>
              </div>
              <div className="text-xs text-blue-500 mt-1 truncate" title={bot.position_sizing.sizing_rationale}>
                {bot.position_sizing.regime_analysis?.regime || 'Dynamic'} market adjustment
              </div>
            </div>
          </div>
        )}

        {/* Coinbase Minimum Trade Warning */}
        {(bot.position_sizing?.final_position_size || bot.position_size_usd || 0) < 10 && (
          <div className="mb-3 p-2 bg-yellow-50 rounded-lg border border-yellow-200">
            <div className="flex items-center space-x-1 mb-1">
              <span className="text-xs font-medium text-yellow-700">⚠️ Coinbase Minimum</span>
            </div>
            <div className="text-xs text-yellow-600">
              ${(bot.position_sizing?.final_position_size || bot.position_size_usd || 0).toFixed(0)} position below $10 minimum - trades may fail
            </div>
          </div>
        )}

        {/* Quick Stats Grid */}
        <div className="grid grid-cols-3 gap-2 text-center">
          <div className="bg-gray-50 rounded-lg p-2">
            <div className="text-xs text-gray-600">Trades</div>
            <div className="font-bold text-sm">{botPnL?.trade_count || 0}</div>
          </div>
          <div className="bg-gray-50 rounded-lg p-2">
            <div className="text-xs text-gray-600">Position</div>
            <div className="font-bold text-sm">${Math.abs(bot.current_position_size || 0).toFixed(0)}</div>
            {/* Add holdings info for compact card */}
            {botPnL && botPnL.current_holdings > 0 && (
              <div className="text-xs text-emerald-600 mt-1">
                {botPnL.current_holdings.toFixed(2)} units
              </div>
            )}
          </div>
          <div className="bg-gray-50 rounded-lg p-2">
            <div className="text-xs text-gray-600">Last Trade</div>
            <div className="font-bold text-sm">
              {bot.last_trade?.minutes_ago ? 
                `${bot.last_trade.minutes_ago < 60 ? 
                  `${bot.last_trade.minutes_ago}m` : 
                  `${Math.floor(bot.last_trade.minutes_ago / 60)}h`
                }` : 'None'
              }
            </div>
          </div>
        </div>

        {/* Status Badge */}
        <div className="flex items-center justify-center mt-3">
          <span className={`px-3 py-1 rounded-full text-xs font-medium ${
            bot.status === 'RUNNING' ? 'bg-green-100 text-green-800' : 'bg-gray-100 text-gray-800'
          }`}>
            {bot.status}
          </span>
        </div>
      </div>
    </div>
  );
};

// Sample 2: Advanced Analytics Card
export const AdvancedAnalyticsCard: React.FC<{ bot: any, pnlData?: any }> = ({ bot, pnlData }) => {
  const botPnL = pnlData?.find((p: any) => p.product_id === bot.pair);
  const { data: trendData } = useTrendAnalysis(bot.pair);
  const trend = trendData || bot.trend_analysis;
  const position = bot.position_sizing;
  
  const getSignalDirection = () => {
    const score = bot.current_combined_score || 0;
    if (score > 0.05) return { icon: <TrendingDown className="h-4 w-4" />, text: 'SELL', color: 'text-red-600 bg-red-50' };
    if (score < -0.05) return { icon: <TrendingUp className="h-4 w-4" />, text: 'BUY', color: 'text-green-600 bg-green-50' };
    return { icon: <Activity className="h-4 w-4" />, text: 'HOLD', color: 'text-yellow-600 bg-yellow-50' };
  };

  const signal = getSignalDirection();
  const isProfit = (botPnL?.net_pnl_usd || 0) >= 0;

  return (
    <div className="bg-white rounded-xl shadow-lg border hover:shadow-xl transition-all duration-300 overflow-hidden">
      {/* Header with Gradient */}
      <div className="bg-gradient-to-r from-indigo-500 to-purple-600 text-white p-4">
        <div className="flex items-center justify-between">
          <div>
            <h3 className="text-lg font-bold">{bot.pair}</h3>
            <p className="text-indigo-100 text-sm">{bot.name}</p>
          </div>
          <div className="text-right">
            <div className="text-lg font-bold">
              {isProfit ? '+' : '-'}${Math.abs(botPnL?.net_pnl_usd || 0).toFixed(2)}
            </div>
            <div className="text-indigo-200 text-xs">
              {botPnL ? `${((botPnL.net_pnl_usd / botPnL.total_spent_usd) * 100).toFixed(1)}% ROI` : 'No trades'}
            </div>
          </div>
        </div>
      </div>

      <div className="p-4">
        {/* Signal Analysis */}
        <div className="mb-4">
          <div className="flex items-center justify-between mb-2">
            <span className="text-sm font-medium text-gray-700">Current Signal</span>
            <div className={`flex items-center space-x-1 px-2 py-1 rounded-lg ${signal.color}`}>
              {signal.icon}
              <span className="text-sm font-medium">{signal.text}</span>
            </div>
          </div>
          
          {/* Signal Strength */}
          <div className="mb-2">
            <div className="flex justify-between text-xs text-gray-600 mb-1">
              <span>Signal Strength</span>
              <span className="font-mono">
                {(bot.current_combined_score || 0).toFixed(3)}
              </span>
            </div>
          </div>
          
          {/* Signal Confidence Meter with 20% Threshold Line */}
          <div className="mb-2">
            <div className="flex items-center justify-between text-xs text-gray-600 mb-1">
              <span>Signal Confidence</span>
              <div className="flex items-center space-x-2">
                <span className="font-mono">{((bot.signal_confidence || 0) * 100).toFixed(1)}%</span>
                {(bot.signal_confidence || 0) < 0.2 && (
                  <span className="text-red-600 font-medium">{'< 20% req'}</span>
                )}
              </div>
            </div>
            <div className="relative h-1.5 bg-gray-200 rounded-full overflow-hidden">
              {/* Confidence Bar */}
              <div 
                className={`h-full transition-all duration-300 ${
                  (bot.signal_confidence || 0) >= 0.2 ? 'bg-green-500' : 'bg-red-500'
                }`}
                style={{ width: `${Math.min((bot.signal_confidence || 0) * 100, 100)}%` }}
              ></div>
              {/* 20% Threshold Line */}
              <div 
                className="absolute top-0 w-0.5 h-full bg-gray-800 opacity-75"
                style={{ left: '20%' }}
                title="20% minimum required"
              ></div>
            </div>
          </div>

          {/* Active Trading Thresholds */}
          {bot.trading_thresholds && (
            <div className="mb-2">
              <div className="flex justify-between text-xs text-gray-600 mb-1">
                <span>Active Thresholds</span>
                <span className="font-mono">
                  {bot.trading_thresholds.buy_threshold?.toFixed(3)} / {bot.trading_thresholds.sell_threshold?.toFixed(3)}
                </span>
              </div>
              <div className="text-xs text-gray-500">
                {bot.trend_analysis?.regime && (
                  <span className="capitalize">{bot.trend_analysis.regime.toLowerCase()} market</span>
                )}
              </div>
            </div>
          )}
        </div>

        {/* Balance Requirements Info - Show ONLY when insufficient balance is blocking trading */}
        {(bot.trade_readiness?.status === 'blocked' && bot.trade_readiness?.blocking_reason?.includes('insufficient_balance')) && (
          <div className="mb-4 p-3 bg-red-50 rounded-lg border border-red-200">
            <div className="flex items-center space-x-1 mb-2">
              <span className="text-sm font-medium text-red-700">💰 Balance Required</span>
            </div>
            <div className="text-xs text-red-600">
              {(() => {
                // Parse specific amounts from blocking reason if available
                const blockingReason = bot.trade_readiness?.blocking_reason || '';
                
                if (bot.trading_intent?.next_action === 'buy') {
                  return <span>Need ${bot.position_size_usd || 25} USD minimum for buy orders</span>;
                } else if (bot.trading_intent?.next_action === 'sell') {
                  // Extract required amount from blocking reason like "Insufficient SUI balance: 5.50000000 available, 7.02760443 required ($25.00 USD)"
                  const requiredMatch = blockingReason.match(/(\d+\.?\d*)\s+required/);
                  const availableMatch = blockingReason.match(/(\d+\.?\d*)\s+available/);
                  const tokenName = bot.pair.split('-')[0];
                  
                  if (requiredMatch && availableMatch) {
                    const required = parseFloat(requiredMatch[1]);
                    const available = parseFloat(availableMatch[1]);
                    const needed = required - available;
                    return <span>Need {needed.toFixed(2)} more {tokenName} (have {available.toFixed(2)}, need {required.toFixed(2)})</span>;
                  } else {
                    return <span>Insufficient {tokenName} holdings for sell orders</span>;
                  }
                } else if (blockingReason.includes('USD')) {
                  return <span>Need ${bot.position_size_usd || 25} USD minimum for buy orders</span>;
                } else {
                  return <span>Insufficient crypto holdings for sell orders</span>;
                }
              })()}
            </div>
          </div>
        )}

        {/* Price Step Indicator - Show when blocked by price step requirement */}
        {(bot.trade_readiness?.status === 'blocked' && bot.trade_readiness?.blocking_reason?.includes('Price step requirement')) && (
          <div className="mb-4 p-3 bg-amber-50 rounded-lg border border-amber-200">
            <div className="flex items-center space-x-1 mb-2">
              <span className="text-sm font-medium text-amber-700">📊 Price Step Required</span>
            </div>
            <div className="text-xs text-amber-600 mb-2">
              {(() => {
                const blockingReason = bot.trade_readiness?.blocking_reason || '';
                // Extract current and required percentages from "Price step requirement not met (0.69% < 0.8%)"
                const stepMatch = blockingReason.match(/\((\d+\.?\d*)%\s*<\s*(\d+\.?\d*)%\)/);
                
                if (stepMatch) {
                  const currentStep = parseFloat(stepMatch[1]);
                  const requiredStep = parseFloat(stepMatch[2]);
                  const progress = Math.min((currentStep / requiredStep) * 100, 100);
                  
                  return (
                    <div>
                      <div className="flex items-center justify-between mb-1">
                        <span>Price change: {currentStep.toFixed(2)}%</span>
                        <span>Required: {requiredStep.toFixed(1)}%</span>
                      </div>
                      <div className="w-full bg-amber-200 rounded-full h-2">
                        <div 
                          className="bg-amber-500 h-2 rounded-full transition-all duration-300"
                          style={{ width: `${progress}%` }}
                        ></div>
                      </div>
                      <div className="mt-1 text-xs">
                        Waiting for {(requiredStep - currentStep).toFixed(2)}% more price movement to trade
                      </div>
                    </div>
                  );
                } else {
                  // Fallback for older format
                  return <span>Waiting for sufficient price movement before next trade</span>;
                }
              })()}
            </div>
          </div>
        )}

        {/* Cooldown Indicator - Show when bot is in post-trade cooldown */}
        {(bot.trade_readiness?.cooldown_remaining_minutes > 0) && (
          <div className="mb-4 p-3 bg-blue-50 rounded-lg border border-blue-200">
            <div className="flex items-center space-x-1 mb-2">
              <span className="text-sm font-medium text-blue-700">⏰ Post-Trade Cooldown</span>
            </div>
            <div className="text-xs text-blue-600">
              {(() => {
                const cooldownMinutes = bot.trade_readiness.cooldown_remaining_minutes;
                const totalCooldown = bot.cooldown_minutes || 15; // Use real cooldown with fallback
                const progress = Math.max(0, ((totalCooldown - cooldownMinutes) / totalCooldown) * 100);
                
                return (
                  <div>
                    <div className="flex items-center justify-between mb-1">
                      <span>Cooldown: {cooldownMinutes} minutes remaining</span>
                      <span>{Math.round(progress)}% complete</span>
                    </div>
                    <div className="w-full bg-blue-200 rounded-full h-2">
                      <div 
                        className="bg-blue-500 h-2 rounded-full transition-all duration-300"
                        style={{ width: `${progress}%` }}
                      ></div>
                    </div>
                    <div className="mt-1 text-xs">
                      Recent trade completed - waiting before next signal evaluation
                    </div>
                  </div>
                );
              })()}
            </div>
          </div>
        )}

        {/* Market Intelligence */}
        {trend && (
          <div className="mb-4 p-3 bg-gray-50 rounded-lg">
            <div className="flex items-center justify-between mb-2">
              <span className="text-sm font-medium text-gray-700 flex items-center">
                <Activity className="h-4 w-4 mr-1" />
                Market Regime
              </span>
              {(() => {
                const direction = getTrendDirection(trend.trend_strength, trend.moving_average_alignment);
                const regimeDisplay = getRegimeDisplay(trend.regime, direction.direction);
                return (
                  <span className={`text-xs px-2 py-1 rounded-full font-medium ${
                    direction.direction === 'UP' ? 'bg-green-100 text-green-800' :
                    direction.direction === 'DOWN' ? 'bg-red-100 text-red-800' :
                    'bg-gray-100 text-gray-800'
                  }`}>
                    {direction.emoji} {regimeDisplay}
                  </span>
                );
              })()}
            </div>
            <div className="grid grid-cols-2 gap-2 text-xs">
              <div>
                <span className="text-gray-600">Trend Strength:</span>
                <span className={`ml-1 font-medium ${
                  trend.trend_strength > 0 ? 'text-green-600' : 
                  trend.trend_strength < 0 ? 'text-red-600' : 'text-gray-600'
                }`}>
                  {trend.trend_strength > 0 ? '+' : ''}{(trend.trend_strength * 100).toFixed(1)}%
                </span>
              </div>
              <div>
                <span className="text-gray-600">Confidence:</span>
                <span className="ml-1 font-medium">{(trend.confidence * 100).toFixed(0)}%</span>
              </div>
            </div>
          </div>
        )}

        {/* Position & Risk */}
        <div className="grid grid-cols-2 gap-3 mb-4">
          <div className="text-center p-2 bg-blue-50 rounded-lg">
            <div className="flex items-center justify-center mb-1">
              <Target className="h-4 w-4 text-blue-600" />
            </div>
            <div className="text-xs text-blue-600 font-medium">Position</div>
            <div className="text-sm font-bold text-blue-800">
              ${Math.abs(bot.current_position_size || 0).toFixed(0)}
            </div>
            <div className="text-xs text-blue-600">
              {position ? `$${position.final_position_size}` : `$${bot.position_size_usd || 20}`} max
            </div>
            {/* Add balance details if available */}
            {botPnL && (
              <div className="text-xs text-blue-500 mt-1">
                {botPnL.current_holdings > 0 
                  ? `${botPnL.current_holdings.toFixed(2)} units`
                  : 'Cash position'
                }
              </div>
            )}
          </div>
          
          <div className="text-center p-2 bg-purple-50 rounded-lg">
            <div className="flex items-center justify-center mb-1">
              <Shield className="h-4 w-4 text-purple-600" />
            </div>
            <div className="text-xs text-purple-600 font-medium">Risk Level</div>
            <div className="text-sm font-bold text-purple-800">
              {position ? 
                `${(position.total_multiplier * 100).toFixed(0)}%` : 
                '100%'
              }
            </div>
            <div className="text-xs text-purple-600">of base</div>
            {position && position.total_multiplier < 1.0 && (
              <div className="text-xs text-purple-500 mt-1">
                ${position.base_position_size} → ${position.final_position_size}
              </div>
            )}
          </div>
        </div>

        {/* Risk Multiplier Breakdown - Show detailed position sizing logic */}
        {position && bot.use_position_sizing && position.total_multiplier < 1.0 && (
          <div className="mb-4 p-3 bg-orange-50 rounded-lg border border-orange-200">
            <div className="flex items-center justify-between mb-2">
              <span className="text-sm font-medium text-orange-700 flex items-center">
                <Zap className="h-4 w-4 mr-1" />
                Position Adjustment
              </span>
              <span className="text-xs text-orange-600">
                {position.regime_analysis?.regime || 'DYNAMIC'}
              </span>
            </div>
            <div className="text-xs text-orange-600 mb-2">
              {position.sizing_rationale || 'Position size adjusted based on market conditions'}
            </div>
            <div className="grid grid-cols-3 gap-2 text-xs">
              <div className="text-center">
                <div className="text-orange-500">Regime</div>
                <div className="font-medium text-orange-800">
                  {position.multiplier_breakdown?.regime_multiplier ? 
                    `${(position.multiplier_breakdown.regime_multiplier * 100).toFixed(0)}%` : 
                    'N/A'
                  }
                </div>
              </div>
              <div className="text-center">
                <div className="text-orange-500">Volatility</div>
                <div className="font-medium text-orange-800">
                  {position.multiplier_breakdown?.volatility_multiplier ? 
                    `${(position.multiplier_breakdown.volatility_multiplier * 100).toFixed(0)}%` : 
                    'N/A'
                  }
                </div>
              </div>
              <div className="text-center">
                <div className="text-orange-500">Confidence</div>
                <div className="font-medium text-orange-800">
                  {position.multiplier_breakdown?.confidence_multiplier ? 
                    `${(position.multiplier_breakdown.confidence_multiplier * 100).toFixed(0)}%` : 
                    'N/A'
                  }
                </div>
              </div>
            </div>
          </div>
        )}

        {/* Coinbase Minimum Trade Warning */}
        {(bot.position_sizing?.final_position_size || bot.position_size_usd || 0) < 10 && (
          <div className="mb-4 p-3 bg-yellow-50 rounded-lg border border-yellow-200">
            <div className="flex items-center justify-between mb-2">
              <span className="text-sm font-medium text-yellow-700 flex items-center">
                <Target className="h-4 w-4 mr-1" />
                Trade Size Warning
              </span>
              <span className="text-xs text-yellow-600">Coinbase Limit</span>
            </div>
            <div className="text-sm text-yellow-600 mb-2">
              Current position size: ${(bot.position_sizing?.final_position_size || bot.position_size_usd || 0).toFixed(2)}
            </div>
            <div className="text-xs text-yellow-600">
              ⚠️ Coinbase requires minimum $10.00 per trade. This bot may experience failed orders until position size increases or market conditions change.
            </div>
          </div>
        )}

        {/* Balance Details - Only show if we have P&L data */}
        {botPnL && botPnL.current_holdings > 0 && (
          <div className="mb-4 p-3 bg-emerald-50 rounded-lg">
            <div className="flex items-center justify-between mb-2">
              <span className="text-sm font-medium text-emerald-700 flex items-center">
                <Target className="h-4 w-4 mr-1" />
                Holdings
              </span>
              <span className="text-xs px-2 py-1 rounded-full bg-emerald-100 text-emerald-800">
                {botPnL.current_holdings.toFixed(4)} {bot.pair.split('-')[0]}
              </span>
            </div>
            <div className="grid grid-cols-2 gap-2 text-xs">
              <div>
                <span className="text-gray-600">Current Value:</span>
                <span className="ml-1 font-medium text-emerald-700">${botPnL.current_value?.toFixed(2)}</span>
              </div>
              <div>
                <span className="text-gray-600">Avg Buy Price:</span>
                <span className="ml-1 font-medium text-emerald-700">${botPnL.average_buy_price?.toFixed(4)}</span>
              </div>
            </div>
          </div>
        )}

        {/* Activity Timeline */}
        <div className="flex items-center justify-between text-xs text-gray-600">
          <div className="flex items-center">
            <Clock className="h-3 w-3 mr-1" />
            Last trade: {bot.last_trade?.minutes_ago ? 
              `${bot.last_trade.minutes_ago < 60 ? 
                `${bot.last_trade.minutes_ago}m ago` : 
                `${Math.floor(bot.last_trade.minutes_ago / 60)}h ago`
              }` : 'None'
            }
          </div>
          <div className={`px-2 py-1 rounded-full text-xs ${
            bot.status === 'RUNNING' ? 'bg-green-100 text-green-700' : 'bg-gray-100 text-gray-700'
          }`}>
            {bot.status}
          </div>
        </div>
      </div>
    </div>
  );
};

// Sample 3: Minimal Modern Card
export const MinimalModernCard: React.FC<{ bot: any, pnlData?: any }> = ({ bot, pnlData }) => {
  const botPnL = pnlData?.find((p: any) => p.product_id === bot.pair);
  const isProfit = (botPnL?.net_pnl_usd || 0) >= 0;
  
  const getTemperatureEmoji = () => {
    switch (bot.temperature) {
      case 'HOT': return '🔥';
      case 'WARM': return '🌡️';
      case 'COOL': return '❄️';
      case 'FROZEN': return '🧊';
      default: return '⚪';
    }
  };

  return (
    <div className="group bg-white rounded-2xl p-6 shadow-sm border border-gray-100 hover:shadow-lg hover:border-gray-200 transition-all duration-300">
      {/* Header */}
      <div className="flex items-center justify-between mb-6">
        <div className="flex items-center space-x-3">
          <div className="text-2xl">{getTemperatureEmoji()}</div>
          <div>
            <h3 className="text-xl font-bold text-gray-900">{bot.pair}</h3>
            <p className="text-sm text-gray-500">{botPnL?.trade_count || 0} trades</p>
          </div>
        </div>
        
        <div className="text-right">
          <div className={`text-2xl font-bold ${isProfit ? 'text-green-600' : 'text-red-600'}`}>
            {isProfit ? '+' : '-'}${Math.abs(botPnL?.net_pnl_usd || 0).toFixed(2)}
          </div>
          <div className="text-sm text-gray-500">
            {botPnL && botPnL.total_spent_usd > 0 ? 
              `${((botPnL.net_pnl_usd / botPnL.total_spent_usd) * 100).toFixed(1)}% ROI` : 
              'No ROI data'
            }
          </div>
        </div>
      </div>

      {/* Signal Visualization */}
      <div className="mb-6">
        <div className="flex items-center justify-between mb-2">
          <span className="text-sm font-medium text-gray-600">Signal Strength</span>
          <span className="text-sm text-gray-900 font-mono">
            {(bot.current_combined_score || 0).toFixed(3)}
          </span>
        </div>
        
        {/* Signal Bar */}
        <div className="relative h-3 bg-gray-100 rounded-full overflow-hidden">
          <div className="absolute inset-0 flex">
            {/* Negative (Buy) side */}
            <div className="flex-1 flex justify-end items-center">
              {(bot.current_combined_score || 0) < 0 && (
                <div 
                  className="h-full bg-gradient-to-r from-green-400 to-green-600 rounded-l-full transition-all duration-500"
                  style={{ width: `${Math.abs(bot.current_combined_score || 0) * 1000}%` }}
                ></div>
              )}
            </div>
            
            {/* Center line */}
            <div className="w-px bg-gray-300"></div>
            
            {/* Positive (Sell) side */}
            <div className="flex-1 flex justify-start items-center">
              {(bot.current_combined_score || 0) > 0 && (
                <div 
                  className="h-full bg-gradient-to-r from-red-400 to-red-600 rounded-r-full transition-all duration-500"
                  style={{ width: `${Math.abs(bot.current_combined_score || 0) * 1000}%` }}
                ></div>
              )}
            </div>
          </div>
        </div>
        
        <div className="flex justify-between text-xs text-gray-400 mt-1">
          <span>BUY</span>
          <span>SELL</span>
        </div>
      </div>

      {/* Status & Activity */}
      <div className="flex items-center justify-between">
        <div className="flex items-center space-x-2">
          <div className={`w-2 h-2 rounded-full ${
            bot.status === 'RUNNING' ? 'bg-green-500 animate-pulse' : 'bg-gray-400'
          }`}></div>
          <span className="text-sm text-gray-600">
            {bot.last_trade?.minutes_ago ? 
              `Active ${bot.last_trade.minutes_ago < 60 ? 
                `${bot.last_trade.minutes_ago}m ago` : 
                `${Math.floor(bot.last_trade.minutes_ago / 60)}h ago`
              }` : 'No recent activity'
            }
          </span>
        </div>
        
        <div className="text-sm font-medium text-gray-900">
          ${Math.abs(bot.current_position_size || 0).toFixed(0)} position
          {/* Add holdings info for minimal card */}
          {botPnL && botPnL.current_holdings > 0 && (
            <div className="text-xs text-emerald-600">
              {botPnL.current_holdings.toFixed(2)} {bot.pair.split('-')[0]}
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

// Sample 4: Metric-Dense Dashboard Card
export const MetricDenseCard: React.FC<{ bot: any, pnlData?: any }> = ({ bot, pnlData }) => {
  const botPnL = pnlData?.find((p: any) => p.product_id === bot.pair);
  const trend = bot.trend_analysis;
  
  const metrics = [
    {
      label: 'P&L',
      value: botPnL ? `${botPnL.net_pnl_usd >= 0 ? '+' : '-'}$${Math.abs(botPnL.net_pnl_usd).toFixed(2)}` : '$0.00',
      color: botPnL && botPnL.net_pnl_usd >= 0 ? 'text-green-600' : 'text-red-600',
      icon: <TrendingUp className="h-3 w-3" />
    },
    {
      label: 'Win Rate',
      value: botPnL && botPnL.trade_count > 0 ? `${((botPnL.sell_trades / botPnL.trade_count) * 100).toFixed(1)}%` : '0%',
      color: 'text-blue-600',
      icon: <Target className="h-3 w-3" />
    },
    {
      label: 'Trades',
      value: `${botPnL?.trade_count || 0}`,
      color: 'text-gray-600',
      icon: <Activity className="h-3 w-3" />
    },
    {
      label: 'Signal',
      value: `${(Math.abs(bot.current_combined_score || 0) * 100).toFixed(1)}%`,
      color: Math.abs(bot.current_combined_score || 0) > 0.05 ? 'text-orange-600' : 'text-gray-600',
      icon: <Zap className="h-3 w-3" />
    },
    {
      label: 'Position',
      value: `$${Math.abs(bot.current_position_size || 0).toFixed(0)}`,
      subValue: botPnL && botPnL.current_holdings > 0 ? `${botPnL.current_holdings.toFixed(2)} ${bot.pair.split('-')[0]}` : null,
      color: 'text-purple-600',
      icon: <Shield className="h-3 w-3" />
    },
    {
      label: 'Confidence',
      value: `${Math.round((bot.trading_intent?.confidence || 0) * 100)}%`,
      color: 'text-indigo-600',
      icon: <TrendingUp className="h-3 w-3" />
    }
  ];

  return (
    <div className="bg-white rounded-lg border shadow-sm hover:shadow-md transition-shadow p-4">
      {/* Header */}
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center space-x-2">
          <h3 className="font-bold text-lg text-gray-900">{bot.pair}</h3>
          <span className="text-lg">
            {bot.temperature === 'HOT' ? '🔥' : 
             bot.temperature === 'WARM' ? '🌡️' : 
             bot.temperature === 'COOL' ? '❄️' : '🧊'}
          </span>
        </div>
        <div className={`px-2 py-1 rounded-full text-xs font-medium ${
          bot.status === 'RUNNING' ? 'bg-green-100 text-green-700' : 'bg-gray-100 text-gray-700'
        }`}>
          {bot.status}
        </div>
      </div>

      {/* Metrics Grid */}
      <div className="grid grid-cols-2 gap-3 mb-4">
        {metrics.map((metric, index) => (
          <div key={index} className="bg-gray-50 rounded-lg p-3">
            <div className="flex items-center justify-between mb-1">
              <span className="text-xs text-gray-600 font-medium">{metric.label}</span>
              <div className={metric.color}>{metric.icon}</div>
            </div>
            <div className={`text-sm font-bold ${metric.color}`}>
              {metric.value}
            </div>
            {/* Add subValue display for holdings info */}
            {metric.subValue && (
              <div className="text-xs text-emerald-600 mt-1">
                {metric.subValue}
              </div>
            )}
          </div>
        ))}
      </div>

      {/* Trend Analysis */}
      {trend && (
        <div className="bg-blue-50 rounded-lg p-3">
          <div className="flex items-center justify-between mb-2">
            <span className="text-xs font-medium text-blue-700">Market Analysis</span>
            <span className="text-xs text-blue-600">{trend.regime}</span>
          </div>
          <div className="flex justify-between text-xs text-blue-600">
            <span>Strength: {(trend.trend_strength * 100).toFixed(1)}%</span>
            <span>Volatility: {trend.timeframe_analysis?.short_term?.volatility ? (trend.timeframe_analysis.short_term.volatility * 100).toFixed(1) + '%' : 'N/A'}</span>
          </div>
        </div>
      )}
    </div>
  );
};

// NEW: Learning-Enhanced Bot Card - Shows universal learning system activity for all 45 bots
export const LearningEnhancedCard: React.FC<{ bot: any, pnlData?: any }> = ({ bot, pnlData }) => {
  const botPnL = pnlData?.find((p: any) => p.product_id === bot.pair);
  const isProfit = (botPnL?.net_pnl_usd || 0) >= 0;
  const winRate = botPnL ? ((botPnL.sell_trades / botPnL.trade_count) * 100).toFixed(1) : '0';
  
  // Extract signal weights from bot configuration
  const signalConfig = bot.signal_config;
  const rsiWeight = signalConfig?.rsi?.weight || 0;
  const maWeight = signalConfig?.moving_average?.weight || 0;
  const macdWeight = signalConfig?.macd?.weight || 0;
  
  // System defaults for comparison (Phase 8 discovery: ALL bots modified)
  const DEFAULT_RSI = 0.40;
  const DEFAULT_MA = 0.35; 
  const DEFAULT_MACD = 0.25;
  
  // Detect learning modifications (universal coverage)
  const hasLearningMods = Math.abs(rsiWeight - DEFAULT_RSI) > 0.01 || 
                         Math.abs(maWeight - DEFAULT_MA) > 0.01 || 
                         Math.abs(macdWeight - DEFAULT_MACD) > 0.01;
                         
  const learningStatus = getUniversalLearningStatus(bot, rsiWeight, maWeight, macdWeight, botPnL);
  
  const getTemperatureColor = () => {
    switch (bot.temperature) {
      case 'HOT': return 'from-red-500 to-orange-500';
      case 'WARM': return 'from-orange-400 to-yellow-400';
      case 'COOL': return 'from-blue-400 to-cyan-400';
      case 'FROZEN': return 'from-gray-400 to-slate-400';
      default: return 'from-gray-300 to-gray-400';
    }
  };

  return (
    <div className="relative overflow-hidden bg-white rounded-xl shadow-lg border hover:shadow-xl transition-all duration-300">
      {/* Temperature + Learning Status Header */}
      <div className={`h-2 bg-gradient-to-r ${getTemperatureColor()}`}></div>
      
      {/* Learning Status Indicator */}
      {hasLearningMods && (
        <div className={`absolute top-2 right-2 px-2 py-1 rounded-full text-xs font-medium ${learningStatus.bgColor} ${learningStatus.textColor} border border-opacity-30`}>
          <div className="flex items-center space-x-1">
            <Brain className="h-3 w-3" />
            <span>{learningStatus.status}</span>
          </div>
        </div>
      )}
      
      <div className="p-4">
        {/* Header Row */}
        <div className="flex items-center justify-between mb-3">
          <div className="flex items-center space-x-2">
            <div className="text-lg font-bold text-gray-900">{bot.pair}</div>
            <span className="text-xl">{bot.temperature === 'HOT' ? '🔥' : bot.temperature === 'WARM' ? '🌡️' : bot.temperature === 'COOL' ? '❄️' : '🧊'}</span>
            {hasLearningMods && <span className="text-sm">🧠</span>}
          </div>
          <div className={`text-right ${isProfit ? 'text-green-600' : 'text-red-600'}`}>
            <div className="text-lg font-bold">
              {isProfit ? '+' : '-'}${Math.abs(botPnL?.net_pnl_usd || 0).toFixed(2)}
            </div>
            <div className="text-xs opacity-75">{winRate}% Win Rate</div>
          </div>
        </div>

        {/* Learning Activity Section */}
        {hasLearningMods && (
          <div className="mb-3 p-3 bg-gradient-to-r from-purple-50 to-blue-50 rounded-lg border border-purple-200">
            <div className="flex items-center justify-between mb-2">
              <span className="text-xs font-medium text-purple-700 flex items-center">
                <BarChart3 className="h-3 w-3 mr-1" />
                Profit-Focused Learning
              </span>
              <span className="text-xs text-purple-600">{learningStatus.strategy}</span>
            </div>
            
            {/* Signal Weight Changes from Defaults */}
            <div className="space-y-1">
              <div className="flex items-center justify-between text-xs">
                <span className="text-gray-600">RSI</span>
                <div className="flex items-center space-x-2">
                  <div className="w-12 h-1.5 bg-gray-200 rounded-full overflow-hidden">
                    <div 
                      className="h-full bg-red-400 rounded-full transition-all duration-300"
                      style={{ width: `${(rsiWeight * 100)}%` }}
                    ></div>
                  </div>
                  <span className="font-mono text-xs w-8">{(rsiWeight * 100).toFixed(0)}%</span>
                  <span className={`text-xs font-medium ${Math.abs(rsiWeight - DEFAULT_RSI) > 0.01 ? 'text-blue-600' : 'text-gray-400'}`}>
                    {rsiWeight !== DEFAULT_RSI ? `(${rsiWeight > DEFAULT_RSI ? '+' : ''}${((rsiWeight - DEFAULT_RSI) * 100).toFixed(0)}%)` : ''}
                  </span>
                </div>
              </div>
              <div className="flex items-center justify-between text-xs">
                <span className="text-gray-600">MA</span>
                <div className="flex items-center space-x-2">
                  <div className="w-12 h-1.5 bg-gray-200 rounded-full overflow-hidden">
                    <div 
                      className="h-full bg-blue-400 rounded-full transition-all duration-300"
                      style={{ width: `${(maWeight * 100)}%` }}
                    ></div>
                  </div>
                  <span className="font-mono text-xs w-8">{(maWeight * 100).toFixed(0)}%</span>
                  <span className={`text-xs font-medium ${Math.abs(maWeight - DEFAULT_MA) > 0.01 ? 'text-blue-600' : 'text-gray-400'}`}>
                    {maWeight !== DEFAULT_MA ? `(${maWeight > DEFAULT_MA ? '+' : ''}${((maWeight - DEFAULT_MA) * 100).toFixed(0)}%)` : ''}
                  </span>
                </div>
              </div>
              <div className="flex items-center justify-between text-xs">
                <span className="text-gray-600">MACD</span>
                <div className="flex items-center space-x-2">
                  <div className="w-12 h-1.5 bg-gray-200 rounded-full overflow-hidden">
                    <div 
                      className="h-full bg-green-400 rounded-full transition-all duration-300"
                      style={{ width: `${(macdWeight * 100)}%` }}
                    ></div>
                  </div>
                  <span className="font-mono text-xs w-8">{(macdWeight * 100).toFixed(0)}%</span>
                  <span className={`text-xs font-medium ${Math.abs(macdWeight - DEFAULT_MACD) > 0.01 ? 'text-blue-600' : 'text-gray-400'}`}>
                    {macdWeight !== DEFAULT_MACD ? `(${macdWeight > DEFAULT_MACD ? '+' : ''}${((macdWeight - DEFAULT_MACD) * 100).toFixed(0)}%)` : ''}
                  </span>
                </div>
              </div>
            </div>
            
            {/* Learning Impact */}
            <div className="mt-2 text-xs text-purple-600">
              {learningStatus.impact}
            </div>
          </div>
        )}

        {/* Signal Strength Visualization */}
        <div className="mb-3">
          <div className="flex items-center justify-between text-xs text-gray-600 mb-1">
            <span>Signal Strength</span>
            <div className="flex items-center space-x-2">
              <span className="font-mono">{(bot.current_combined_score || 0).toFixed(3)}</span>
              <span>({(Math.abs(bot.current_combined_score || 0) * 100).toFixed(1)}%)</span>
            </div>
          </div>
          <div className="h-2 bg-gray-200 rounded-full overflow-hidden">
            <div 
              className={`h-full transition-all duration-500 ${
                (bot.current_combined_score || 0) > 0 
                  ? 'bg-gradient-to-r from-green-400 to-green-500' 
                  : 'bg-gradient-to-r from-red-400 to-red-500'
              }`}
              style={{ 
                width: `${Math.abs(bot.current_combined_score || 0) * 100}%`,
                marginLeft: (bot.current_combined_score || 0) < 0 ? `${100 - Math.abs(bot.current_combined_score || 0) * 100}%` : '0%'
              }}
            ></div>
          </div>
        </div>

        {/* Quick Stats Grid */}
        <div className="grid grid-cols-3 gap-2 text-center">
          <div className="bg-gray-50 rounded-lg p-2">
            <div className="text-xs text-gray-600">Trades</div>
            <div className="font-bold text-sm">{botPnL?.trade_count || 0}</div>
          </div>
          <div className="bg-gray-50 rounded-lg p-2">
            <div className="text-xs text-gray-600">Position</div>
            <div className="font-bold text-sm">${Math.abs(bot.current_position_size || 0).toFixed(0)}</div>
          </div>
          <div className="bg-gray-50 rounded-lg p-2">
            <div className="text-xs text-gray-600">Holdings</div>
            <div className="font-bold text-sm">{(bot.current_holdings || 0).toFixed(2)}</div>
          </div>
        </div>
      </div>
    </div>
  );
};

// Helper function to determine universal learning status for any bot
function getUniversalLearningStatus(_bot: any, rsiWeight: number, maWeight: number, macdWeight: number, botPnL: any) {
  const DEFAULT_RSI = 0.40;
  const DEFAULT_MA = 0.35;
  const DEFAULT_MACD = 0.25;
  
  // Calculate changes from defaults
  const rsiChange = rsiWeight - DEFAULT_RSI;
  const maChange = maWeight - DEFAULT_MA;
  const macdChange = macdWeight - DEFAULT_MACD;
  
  // Determine strategy based on actual changes and P&L
  const netPnL = botPnL?.net_pnl_usd || 0;
  let strategy = "Pattern-Based";
  let bgColor = "bg-purple-100";
  let textColor = "text-purple-700";
  let impact = "Optimized signal weights";
  
  // Aggressive changes (large reductions in RSI or big increases in MA)
  if (Math.abs(rsiChange) > 0.15 || Math.abs(maChange) > 0.15) {
    if (netPnL < -5) {
      strategy = "Aggressive Rebalance";
      bgColor = "bg-red-100";
      textColor = "text-red-700"; 
      impact = rsiChange < -0.1 ? "Major RSI reduction for losses" : "Major rebalancing for recovery";
    } else {
      strategy = "Major Moderate";
      bgColor = "bg-orange-100";
      textColor = "text-orange-700";
      impact = "Significant strategy adjustment";
    }
  }
  // Moderate changes
  else if (Math.abs(rsiChange) > 0.05 || Math.abs(macdChange) > 0.05) {
    if (netPnL < -2) {
      strategy = "Moderate Rebalance";
      bgColor = "bg-orange-100";
      textColor = "text-orange-700";
      impact = "Balanced adjustment for improvement";
    } else if (netPnL > 1) {
      strategy = "Winner Optimization";
      bgColor = "bg-green-100";
      textColor = "text-green-700";
      impact = "Fine-tuned winning strategy";
    }
  }
  // Minor adjustments
  else if (Math.abs(rsiChange) > 0.01 || Math.abs(maChange) > 0.01 || Math.abs(macdChange) > 0.01) {
    if (netPnL > 0.5) {
      strategy = "Winner Enhancement";
      bgColor = "bg-emerald-100";
      textColor = "text-emerald-700";
      impact = "Polished winning approach";
    } else {
      strategy = "Minor Adjustment";
      bgColor = "bg-blue-100";
      textColor = "text-blue-700";
      impact = "Gentle optimization";
    }
  }

  return {
    status: "Learning",
    strategy,
    impact,
    bgColor,
    textColor
  };
}

export default {
  CompactPerformanceCard,
  AdvancedAnalyticsCard,
  MinimalModernCard,
  MetricDenseCard,
  LearningEnhancedCard
};