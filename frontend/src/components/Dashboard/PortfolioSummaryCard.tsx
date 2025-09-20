import React from 'react';
import { useLivePortfolio } from '../../hooks/useLivePortfolio';
import { useCleanProductPerformance } from '../../hooks/useCleanTrades';
import { DataFreshnessIndicator } from '../DataFreshnessIndicators';

interface PortfolioSummaryCardProps {
  className?: string;
}

/**
 * Enhanced portfolio summary card for Phase 2 grid layout
 * Features:
 * - Large, prominent display optimized for 2-column grid space
 * - Live Coinbase data as source of truth
 * - Enhanced visual hierarchy with larger typography
 * - Gradient backgrounds based on P&L performance
 * - Clear breakdown of cash vs crypto allocation
 */
export const PortfolioSummaryCard: React.FC<PortfolioSummaryCardProps> = ({ 
  className = '' 
}) => {
  // Get live portfolio data from Coinbase (source of truth for current value)
  const { data: livePortfolioData, isLoading: isLiveLoading, dataUpdatedAt: liveUpdatedAt } = useLivePortfolio();
  
  // Get historical performance data for P&L calculations
  const { data: performanceData, isLoading: isPerfLoading } = useCleanProductPerformance();

  const isLoading = isLiveLoading || isPerfLoading;

  if (isLoading) {
    return (
      <div className={`
        bg-white rounded-xl shadow-lg border-2 p-8 h-80
        animate-pulse
        ${className}
      `}>
        <div className="space-y-6">
          <div className="h-8 bg-gray-200 rounded w-1/2"></div>
          <div className="h-16 bg-gray-200 rounded w-3/4"></div>
          <div className="h-12 bg-gray-200 rounded w-2/3"></div>
          <div className="grid grid-cols-2 gap-4">
            <div className="h-16 bg-gray-200 rounded"></div>
            <div className="h-16 bg-gray-200 rounded"></div>
          </div>
        </div>
      </div>
    );
  }

  // Calculate portfolio metrics using LIVE Coinbase data as source of truth
  const totalValue = livePortfolioData?.total_portfolio_value_usd || 0;
  const usdCash = livePortfolioData?.holdings?.find((h: any) => h.currency === 'USD')?.value_usd || 0;
  const cryptoValue = totalValue - usdCash;
  
  // Calculate historical P&L from database (for trend analysis only)
  const totalPnL = performanceData?.products?.reduce((sum: number, product: any) => 
    sum + (product.net_pnl_usd || 0), 0) || 0;
  
  // Use live holdings count instead of database
  const activePairs = livePortfolioData?.holdings?.filter((h: any) => h.currency !== 'USD' && h.currency !== 'USDC').length || 0;

  // Determine P&L styling with enhanced gradients
  const isProfit = totalPnL >= 0;
  const bgGradient = isProfit 
    ? 'bg-gradient-to-br from-green-50 via-emerald-50 to-green-100 border-green-300' 
    : 'bg-gradient-to-br from-red-50 via-rose-50 to-red-100 border-red-300';

  return (
    <div className={`
      ${bgGradient}
      rounded-xl shadow-xl border-2 p-8 h-80
      transition-all duration-300 hover:shadow-2xl
      ${className}
    `}>
      {/* Header - Enhanced */}
      <div className="flex items-center justify-between mb-6">
        <div className="flex items-center space-x-3">
          <h2 className="text-2xl font-bold text-gray-900">Portfolio</h2>
          <span className="text-3xl">💰</span>
          <span className="px-3 py-1 bg-blue-100 text-blue-800 text-sm font-medium rounded-full">
            LIVE
          </span>
        </div>
        <DataFreshnessIndicator 
          lastUpdated={new Date(liveUpdatedAt || Date.now())}
          size="sm"
          freshThresholdSeconds={15}
          staleThresholdSeconds={30}
        />
      </div>

      {/* Total Value - Extra Large Prominence */}
      <div className="mb-8">
        <div className="text-sm font-medium text-gray-600 mb-2">Total Portfolio Value</div>
        <div className="text-5xl font-bold text-gray-900 tracking-tight">
          ${totalValue.toFixed(2)}
        </div>
        <div className="text-xs text-gray-500 mt-1">
          Source: Coinbase Real-time
        </div>
      </div>

      {/* Portfolio Allocation - Enhanced Grid Layout */}
      <div className="grid grid-cols-2 gap-6 mb-6">
        <div className="text-center">
          <div className="text-sm font-medium text-gray-600 mb-1">Cash (USD)</div>
          <div className="text-2xl font-bold text-blue-600">${usdCash.toFixed(0)}</div>
          <div className="text-xs text-gray-500">
            {((usdCash / totalValue) * 100).toFixed(1)}%
          </div>
        </div>
        <div className="text-center">
          <div className="text-sm font-medium text-gray-600 mb-1">Crypto Value</div>
          <div className="text-2xl font-bold text-purple-600">${cryptoValue.toFixed(0)}</div>
          <div className="text-xs text-gray-500">
            {((cryptoValue / totalValue) * 100).toFixed(1)}%
          </div>
        </div>
      </div>

      {/* Performance & Activity Indicators */}
      <div className="grid grid-cols-2 gap-4">
        <div className="text-center p-3 bg-white bg-opacity-50 rounded-lg">
          <div className="text-sm font-medium text-gray-600">Total P&L</div>
          <div className={`text-xl font-bold ${
            isProfit ? 'text-green-600' : 'text-red-600'
          }`}>
            {isProfit ? '+' : ''}${totalPnL.toFixed(2)}
          </div>
        </div>
        <div className="text-center p-3 bg-white bg-opacity-50 rounded-lg">
          <div className="text-sm font-medium text-gray-600">Active Pairs</div>
          <div className="text-xl font-bold text-gray-900">{activePairs}</div>
        </div>
      </div>
    </div>
  );
};

export default PortfolioSummaryCard;
