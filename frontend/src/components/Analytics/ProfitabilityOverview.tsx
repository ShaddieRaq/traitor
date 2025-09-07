import React from 'react';
import { TrendingUp, TrendingDown, DollarSign, Activity, BarChart3 } from 'lucide-react';

interface ProfitabilityData {
  total_trades: number;
  total_volume_usd: number;
  net_pnl: number;
  roi_percentage: number;
  daily_pnl?: number;
  weekly_pnl?: number;
  current_balance_usd: number;
  active_positions_value: number;
}

interface ProfitabilityOverviewProps {
  data?: ProfitabilityData;
  isLoading?: boolean;
}

const ProfitabilityOverview: React.FC<ProfitabilityOverviewProps> = ({ 
  data, 
  isLoading = false 
}) => {
  if (isLoading) {
    return (
      <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
        <div className="animate-pulse">
          <div className="h-6 bg-gray-200 rounded w-48 mb-4"></div>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            {[1, 2, 3, 4].map((i) => (
              <div key={i} className="space-y-2">
                <div className="h-4 bg-gray-200 rounded w-20"></div>
                <div className="h-8 bg-gray-200 rounded w-24"></div>
              </div>
            ))}
          </div>
        </div>
      </div>
    );
  }

  if (!data) {
    return (
      <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
        <div className="text-center text-gray-500">
          <BarChart3 className="mx-auto h-12 w-12 text-gray-300 mb-2" />
          <p>P&L data not available</p>
        </div>
      </div>
    );
  }

  const formatCurrency = (amount: number) => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
      minimumFractionDigits: 2,
      maximumFractionDigits: 2,
    }).format(amount);
  };

  const formatPercentage = (percentage: number) => {
    return `${percentage >= 0 ? '+' : ''}${percentage.toFixed(2)}%`;
  };

  const getPnLColor = (amount: number) => {
    if (amount > 0) return 'text-green-600';
    if (amount < 0) return 'text-red-600';
    return 'text-gray-600';
  };

  const getPnLIcon = (amount: number) => {
    return amount >= 0 ? TrendingUp : TrendingDown;
  };

  const totalPortfolioValue = data.current_balance_usd + data.active_positions_value;

  return (
    <div className="bg-white rounded-lg shadow-sm border border-gray-200">
      {/* Header */}
      <div className="px-6 py-4 border-b border-gray-200">
        <div className="flex items-center justify-between">
          <h3 className="text-lg font-semibold text-gray-900 flex items-center">
            <BarChart3 className="h-5 w-5 mr-2 text-blue-600" />
            Profitability Overview
          </h3>
          <div className="text-sm text-gray-500">
            {data.total_trades.toLocaleString()} total trades
          </div>
        </div>
      </div>

      {/* Main Metrics Grid */}
      <div className="p-6">
        <div className="grid grid-cols-2 md:grid-cols-4 gap-6 mb-6">
          {/* Net P&L */}
          <div className="text-center">
            <div className="flex items-center justify-center mb-2">
              {React.createElement(getPnLIcon(data.net_pnl), {
                className: `h-5 w-5 ${getPnLColor(data.net_pnl)}`
              })}
            </div>
            <div className="text-xs text-gray-500 uppercase tracking-wide mb-1">Net P&L</div>
            <div className={`text-2xl font-bold ${getPnLColor(data.net_pnl)}`}>
              {formatCurrency(data.net_pnl)}
            </div>
            <div className={`text-sm ${getPnLColor(data.roi_percentage)}`}>
              {formatPercentage(data.roi_percentage)}
            </div>
          </div>

          {/* Portfolio Value */}
          <div className="text-center">
            <div className="flex items-center justify-center mb-2">
              <DollarSign className="h-5 w-5 text-blue-600" />
            </div>
            <div className="text-xs text-gray-500 uppercase tracking-wide mb-1">Portfolio</div>
            <div className="text-2xl font-bold text-gray-900">
              {formatCurrency(totalPortfolioValue)}
            </div>
            <div className="text-sm text-gray-500">
              Cash: {formatCurrency(data.current_balance_usd)}
            </div>
          </div>

          {/* Volume */}
          <div className="text-center">
            <div className="flex items-center justify-center mb-2">
              <Activity className="h-5 w-5 text-purple-600" />
            </div>
            <div className="text-xs text-gray-500 uppercase tracking-wide mb-1">Volume</div>
            <div className="text-2xl font-bold text-gray-900">
              {formatCurrency(data.total_volume_usd)}
            </div>
            <div className="text-sm text-gray-500">
              Avg: {formatCurrency(data.total_volume_usd / data.total_trades)}
            </div>
          </div>
        </div>

        {/* Recent Performance */}
        {(data.daily_pnl !== undefined || data.weekly_pnl !== undefined) && (
          <div className="border-t border-gray-200 pt-4">
            <div className="text-sm font-medium text-gray-700 mb-3">Recent Performance</div>
            <div className="flex space-x-6">
              {data.daily_pnl !== undefined && (
                <div className="flex items-center space-x-2">
                  <span className="text-sm text-gray-500">24h:</span>
                  <span className={`text-sm font-medium ${getPnLColor(data.daily_pnl)}`}>
                    {formatCurrency(data.daily_pnl)}
                  </span>
                </div>
              )}
              {data.weekly_pnl !== undefined && (
                <div className="flex items-center space-x-2">
                  <span className="text-sm text-gray-500">7d:</span>
                  <span className={`text-sm font-medium ${getPnLColor(data.weekly_pnl)}`}>
                    {formatCurrency(data.weekly_pnl)}
                  </span>
                </div>
              )}
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default ProfitabilityOverview;
