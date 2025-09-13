import React from 'react';
import { useBotPerformanceByPair } from '../../hooks/useBotPerformance';

interface BotPerformanceSectionProps {
  productId: string;
  isLoading?: boolean;
  compact?: boolean;
}

const BotPerformanceSection: React.FC<BotPerformanceSectionProps> = ({ 
  productId, 
  isLoading: externalLoading = false,
  compact = false 
}) => {
  // Use the correct bot performance API instead of broken positions API
  const { data: performance, isLoading: performanceLoading } = useBotPerformanceByPair(productId);
  
  const isLoading = externalLoading || performanceLoading;
  
  if (isLoading) {
    return (
      <div className="mb-3 p-3 bg-gray-50 rounded border animate-pulse">
        <div className="h-4 bg-gray-200 rounded mb-2"></div>
        <div className="grid grid-cols-2 gap-3">
          <div className="h-8 bg-gray-200 rounded"></div>
          <div className="h-8 bg-gray-200 rounded"></div>
          <div className="h-8 bg-gray-200 rounded"></div>
          <div className="h-8 bg-gray-200 rounded"></div>
        </div>
      </div>
    );
  }

  if (!performance) {
    return (
      <div className="mb-3 p-3 bg-gray-50 rounded border">
        <div className="text-xs text-gray-500 text-center">
          No performance data available for {productId}
        </div>
      </div>
    );
  }

  const isProfitable = performance.total_pnl >= 0;
  const profitColor = isProfitable ? 'text-green-600' : 'text-red-600';
  
  // Format large numbers
  const formatNumber = (num: number, decimals: number = 2) => {
    if (Math.abs(num) >= 1000) {
      return `${(num / 1000).toFixed(1)}k`;
    }
    return num.toFixed(decimals);
  };

  const formatCurrency = (amount: number) => {
    return `$${formatNumber(amount)}`;
  };

  const formatQuantity = (quantity: number) => {
    if (quantity >= 1000000) {
      return `${(quantity / 1000000).toFixed(1)}M`;
    } else if (quantity >= 1000) {
      return `${(quantity / 1000).toFixed(1)}k`;
    } else if (quantity >= 1) {
      return quantity.toFixed(1);
    } else {
      return quantity.toFixed(6);
    }
  };

  if (compact) {
    return (
      <div className="mb-3 p-2 bg-gray-50 rounded border">
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-4 text-sm">
            <div>
              <span className="text-gray-500">P&L: </span>
              <span className={`font-medium ${profitColor}`}>
                {formatCurrency(performance.total_pnl)}
              </span>
            </div>
            <div>
              <span className="text-gray-500">ROI: </span>
              <span className={`font-medium ${profitColor}`}>
                {performance.roi_percentage.toFixed(1)}%
              </span>
            </div>
            <div>
              <span className="text-gray-500">Trades: </span>
              <span className="font-medium text-gray-900">
                {performance.trade_count}
              </span>
            </div>
          </div>
          <div className="text-xs text-gray-400">
            {formatQuantity(performance.current_position)} coins
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="mb-3 p-3 bg-gray-50 rounded border">
      <div className="flex items-center justify-between mb-2">
        <div className="flex items-center space-x-2">
          <span className="text-sm font-medium text-gray-600">📊 Position</span>
          <div className={`text-xs px-2 py-1 rounded ${
            isProfitable ? 'bg-green-100 text-green-700' : 'bg-red-100 text-red-700'
          }`}>
            {isProfitable ? '📈 Profit' : '📉 Loss'}
          </div>
        </div>
        <span className="text-xs text-gray-400">{performance.trade_count} trades</span>
      </div>
      
      <div className="grid grid-cols-2 gap-3 text-sm">
        <div className="space-y-1">
          <div className="text-xs text-gray-500">Total P&L</div>
          <div className={`font-semibold text-lg ${profitColor}`}>
            {formatCurrency(performance.total_pnl)}
          </div>
        </div>
        
        <div className="space-y-1">
          <div className="text-xs text-gray-500">ROI</div>
          <div className={`font-semibold text-lg ${profitColor}`}>
            {performance.roi_percentage.toFixed(1)}%
          </div>
        </div>
        
        <div className="space-y-1">
          <div className="text-xs text-gray-500">Position Size</div>
          <div className="font-medium text-gray-900">
            {formatQuantity(performance.current_position)}
            <span className="text-xs text-gray-500 ml-1">coins</span>
          </div>
          <div className="text-xs text-gray-500">
            Current Price: ${performance.current_price?.toFixed(4) || '0.0000'}
          </div>
        </div>
        
        <div className="space-y-1">
          <div className="text-xs text-gray-500">Avg Entry</div>
          <div className="font-medium text-gray-900">
            {formatCurrency(performance.average_entry_price)}
          </div>
        </div>
      </div>

      {/* Additional metrics row */}
      <div className="mt-2 pt-2 border-t border-gray-200">
        <div className="grid grid-cols-3 gap-2 text-xs">
          <div>
            <span className="text-gray-500">Realized: </span>
            <span className={`font-medium ${performance.realized_pnl >= 0 ? 'text-green-600' : 'text-red-600'}`}>
              {formatCurrency(performance.realized_pnl)}
            </span>
          </div>
          <div>
            <span className="text-gray-500">Unrealized: </span>
            <span className={`font-medium ${performance.unrealized_pnl >= 0 ? 'text-green-600' : 'text-red-600'}`}>
              {formatCurrency(performance.unrealized_pnl)}
            </span>
          </div>
          <div>
            <span className="text-gray-500">Fees: </span>
            <span className="font-medium text-red-600">
              {formatCurrency(performance.total_fees)}
            </span>
          </div>
        </div>
      </div>
    </div>
  );
};

export default BotPerformanceSection;
