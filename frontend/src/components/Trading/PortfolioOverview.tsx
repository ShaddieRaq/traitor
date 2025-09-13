import React from 'react';
import { usePositionSummary, usePositionTracking } from '../../hooks/usePositionTracking';

const PortfolioOverview: React.FC = () => {
  const { data: summary, isLoading: summaryLoading } = usePositionSummary();
  const { data: positions, isLoading: positionsLoading } = usePositionTracking();

  const isLoading = summaryLoading || positionsLoading;

  if (isLoading) {
    return (
      <div className="mb-6 p-4 bg-white rounded-lg shadow border animate-pulse">
        <div className="h-6 bg-gray-200 rounded mb-4"></div>
        <div className="grid grid-cols-3 gap-4">
          <div className="h-16 bg-gray-200 rounded"></div>
          <div className="h-16 bg-gray-200 rounded"></div>
          <div className="h-16 bg-gray-200 rounded"></div>
        </div>
      </div>
    );
  }

  if (!summary || !positions) {
    return (
      <div className="mb-6 p-4 bg-white rounded-lg shadow border">
        <div className="text-center text-gray-500">
          No portfolio data available
        </div>
      </div>
    );
  }

  const formatCurrency = (amount: number | undefined) => {
    if (amount === undefined || amount === null) return '$0.00';
    return `$${amount.toFixed(2)}`;
  };

  // Add null checks before accessing summary properties
  if (!summary) {
    return (
      <div className="mb-6 p-4 bg-white rounded-lg shadow border">
        <div className="text-center text-gray-500">
          No portfolio data available
        </div>
      </div>
    );
  }

  const isProfitable = summary.total_pnl >= 0;
  const profitColor = isProfitable ? 'text-green-600' : 'text-red-600';
  const profitBg = isProfitable ? 'bg-green-50 border-green-200' : 'bg-red-50 border-red-200';

  return (
    <div className="mb-6 p-4 bg-white rounded-lg shadow border">
      {/* Header */}
      <div className="flex items-center justify-between mb-4">
        <h2 className="text-lg font-semibold text-gray-900">💼 Portfolio Overview</h2>
        <div className={`px-3 py-1 rounded-full border ${profitBg}`}>
          <span className={`text-sm font-medium ${profitColor}`}>
            {isProfitable ? '📈 Profitable' : '📉 Loss'}
          </span>
        </div>
      </div>

      {/* Summary Cards */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-4">
        <div className="p-4 bg-gray-50 rounded-lg">
          <div className="text-xs text-gray-500 uppercase tracking-wide mb-1">Total P&L</div>
          <div className={`text-2xl font-bold ${profitColor}`}>
            {formatCurrency(summary.total_pnl)}
          </div>
          <div className="text-xs text-gray-500">
            Realized: {formatCurrency(summary.total_realized_pnl)} | 
            Unrealized: {formatCurrency(summary.total_unrealized_pnl)}
          </div>
        </div>

        <div className="p-4 bg-gray-50 rounded-lg">
          <div className="text-xs text-gray-500 uppercase tracking-wide mb-1">Trading Activity</div>
          <div className="text-2xl font-bold text-gray-900">
            {summary.total_trades}
          </div>
          <div className="text-xs text-gray-500">
            Total Trades Executed
          </div>
        </div>

        <div className="p-4 bg-gray-50 rounded-lg">
          <div className="text-xs text-gray-500 uppercase tracking-wide mb-1">Active Positions</div>
          <div className="text-2xl font-bold text-gray-900">
            {summary.open_positions_count}
          </div>
          <div className="text-xs text-gray-500">
            {summary.products_traded} products traded total
          </div>
        </div>
      </div>

      {/* Top Performers */}
      {positions && positions.length > 0 && (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {/* Most Profitable Position */}
          {(() => {
            const topPerformer = positions
              .filter(p => p.current_quantity > 0)
              .sort((a, b) => b.total_pnl - a.total_pnl)[0];
            
            return topPerformer && topPerformer.total_pnl > 0 ? (
              <div className="p-3 bg-green-50 rounded-lg border border-green-200">
                <div className="text-xs text-green-700 font-medium mb-1">🏆 Top Performer</div>
                <div className="font-semibold text-green-900">
                  {topPerformer.product_id}
                </div>
                <div className="text-sm text-green-700">
                  {formatCurrency(topPerformer.total_pnl)}
                </div>
              </div>
            ) : null;
          })()}

          {/* Biggest Loss Position */}
          {(() => {
            const worstPerformer = positions
              .filter(p => p.current_quantity > 0)
              .sort((a, b) => a.total_pnl - b.total_pnl)[0];
            
            return worstPerformer && worstPerformer.total_pnl < 0 ? (
              <div className="p-3 bg-red-50 rounded-lg border border-red-200">
                <div className="text-xs text-red-700 font-medium mb-1">📉 Needs Attention</div>
                <div className="font-semibold text-red-900">
                  {worstPerformer.product_id}
                </div>
                <div className="text-sm text-red-700">
                  {formatCurrency(worstPerformer.total_pnl)}
                </div>
              </div>
            ) : null;
          })()}
        </div>
      )}
    </div>
  );
};

export default PortfolioOverview;
