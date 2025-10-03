import React from 'react';
import { TrendingUp, TrendingDown, Activity, Clock, Target, Shield, Zap } from 'lucide-react';

// Sample 1: Compact Performance-Focused Card
export const CompactPerformanceCard: React.FC<{ bot: any, pnlData?: any }> = ({ bot, pnlData }) => {
  const botPnL = pnlData?.products?.find((p: any) => p.product_id === bot.pair);
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
              {isProfit ? '+' : ''}${Math.abs(botPnL?.net_pnl_usd || 0).toFixed(2)}
            </div>
            <div className="text-xs opacity-75">{winRate}% Win Rate</div>
          </div>
        </div>

        {/* Signal Strength Visualization */}
        <div className="mb-3">
          <div className="flex items-center justify-between text-xs text-gray-600 mb-1">
            <span>Signal Strength</span>
            <span>{(Math.abs(bot.current_combined_score || 0) * 100).toFixed(1)}%</span>
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
  const botPnL = pnlData?.products?.find((p: any) => p.product_id === bot.pair);
  const trend = bot.trend_analysis;
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
              {isProfit ? '+' : ''}${Math.abs(botPnL?.net_pnl_usd || 0).toFixed(2)}
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
          
          {/* Confidence Meter */}
          <div className="mb-2">
            <div className="flex justify-between text-xs text-gray-600 mb-1">
              <span>Confidence</span>
              <span>{Math.round((bot.trading_intent?.confidence || 0) * 100)}%</span>
            </div>
            <div className="h-1.5 bg-gray-200 rounded-full">
              <div 
                className="h-full bg-blue-500 rounded-full transition-all duration-300"
                style={{ width: `${(bot.trading_intent?.confidence || 0) * 100}%` }}
              ></div>
            </div>
          </div>
        </div>

        {/* Market Intelligence */}
        {trend && (
          <div className="mb-4 p-3 bg-gray-50 rounded-lg">
            <div className="flex items-center justify-between mb-2">
              <span className="text-sm font-medium text-gray-700 flex items-center">
                <Activity className="h-4 w-4 mr-1" />
                Market Regime
              </span>
              <span className={`text-xs px-2 py-1 rounded-full ${
                trend.regime === 'TRENDING' ? 'bg-blue-100 text-blue-800' : 'bg-orange-100 text-orange-800'
              }`}>
                {trend.regime}
              </span>
            </div>
            <div className="grid grid-cols-2 gap-2 text-xs">
              <div>
                <span className="text-gray-600">Trend Strength:</span>
                <span className="ml-1 font-medium">{(trend.trend_strength * 100).toFixed(1)}%</span>
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
          </div>
        </div>

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
  const botPnL = pnlData?.products?.find((p: any) => p.product_id === bot.pair);
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
            {isProfit ? '+' : ''}${Math.abs(botPnL?.net_pnl_usd || 0).toFixed(2)}
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
        </div>
      </div>
    </div>
  );
};

// Sample 4: Metric-Dense Dashboard Card
export const MetricDenseCard: React.FC<{ bot: any, pnlData?: any }> = ({ bot, pnlData }) => {
  const botPnL = pnlData?.products?.find((p: any) => p.product_id === bot.pair);
  const trend = bot.trend_analysis;
  const position = bot.position_sizing;
  
  const metrics = [
    {
      label: 'P&L',
      value: botPnL ? `${botPnL.net_pnl_usd >= 0 ? '+' : ''}$${Math.abs(botPnL.net_pnl_usd).toFixed(2)}` : '$0.00',
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

export default {
  CompactPerformanceCard,
  AdvancedAnalyticsCard,
  MinimalModernCard,
  MetricDenseCard
};