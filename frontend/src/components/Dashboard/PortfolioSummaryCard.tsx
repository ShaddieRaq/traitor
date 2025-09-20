import React from 'react';
import { useLivePortfolio } from '../../hooks/useLivePortfolio';
import { useCleanProductPerformance } from '../../hooks/useCleanTrades';
import PerformanceTrend from './PerformanceTrend';
import { DataFreshnessIndicator } from '../DataFreshnessIndicators';

interface PortfolioSummaryCardProps {
  className?: string;
}

/**
 * Large, prominent portfolio summary card showing total value and P&L
 * Now uses LIVE Coinbase data as the source of truth for current portfolio value
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
        bg-white rounded-lg shadow-lg border p-6 
        animate-pulse
        ${className}
      `}>
        <div className="space-y-4">
          <div className="h-6 bg-gray-200 rounded w-1/3"></div>
          <div className="h-12 bg-gray-200 rounded w-2/3"></div>
          <div className="h-8 bg-gray-200 rounded w-1/2"></div>
          <div className="h-16 bg-gray-200 rounded"></div>
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

  // Generate mock trend data based on current performance
  const generateTrendData = () => {
    const points = 12; // 12 data points
    return Array.from({ length: points }, (_, i) => {
      const progress = i / (points - 1);
      const baseValue = totalValue * 0.8; // Start from 80% of current value
      const currentTrend = baseValue + (totalValue * 0.2 * progress);
      const noise = (Math.random() - 0.5) * totalValue * 0.05; // Small noise
      return Math.max(0, currentTrend + noise);
    });
  };

  // Determine P&L styling
  const isProfit = totalPnL >= 0;
  const bgGradient = isProfit 
    ? 'bg-gradient-to-br from-green-50 to-emerald-50 border-green-200' 
    : 'bg-gradient-to-br from-red-50 to-rose-50 border-red-200';

  return (
    <div className={`
      ${bgGradient}
      rounded-lg shadow-lg border-2 p-6
      ${className}
    `}>
      {/* Header */}
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center space-x-2">
          <h2 className="text-lg font-semibold text-gray-900">Portfolio</h2>
          <span className="text-2xl">💰</span>
          <span className="px-2 py-1 bg-blue-100 text-blue-800 text-xs rounded-full">
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

      {/* Total Value - Large Prominence - NOW USING LIVE DATA */}
      <div className="mb-6">
        <div className="text-sm text-gray-600 mb-1">Total Portfolio Value (Live)</div>
        <div className="text-4xl font-bold text-gray-900">
          ${totalValue.toFixed(2)}
        </div>
        <div className="text-xs text-gray-500 mt-1">
          Source: Coinbase Real-time
        </div>
      </div>

      {/* P&L Section with Trend Charts */}
      <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 mb-4">
        <div>
          <PerformanceTrend
            title="Total P&L"
            currentValue={totalPnL}
            change={totalPnL}
            format="currency"
            historicalData={generateTrendData()}
            size="md"
            showChart={true}
          />
        </div>
        <div>
          <PerformanceTrend
            title="Return %"
            currentValue={totalPnL}
            changePercent={totalPnL > 0 ? 15 : -5} // Mock percentage
            format="percentage"
            size="md"
            showChart={false}
          />
        </div>
      </div>

      {/* Secondary Stats */}
      <div className="grid grid-cols-3 gap-4 pt-4 border-t border-gray-200">
        <div>
          <div className="text-sm text-gray-600">Active Pairs</div>
          <div className="text-lg font-semibold text-gray-900">{activePairs}</div>
        </div>
        <div>
          <div className="text-sm text-gray-600">Cash (USD)</div>
          <div className="text-lg font-semibold text-gray-900">${usdCash.toFixed(0)}</div>
        </div>
        <div>
          <div className="text-sm text-gray-600">Crypto Value</div>
          <div className="text-lg font-semibold text-gray-900">${cryptoValue.toFixed(0)}</div>
        </div>
      </div>

      {/* Performance Indicator */}
      <div className="mt-4 pt-4 border-t border-gray-200">
        <div className="flex items-center justify-between">
          <span className="text-sm text-gray-600">Performance</span>
          <div className="flex items-center space-x-2">
            <span className={`text-xs px-2 py-1 rounded-full ${
              isProfit 
                ? 'bg-green-100 text-green-800' 
                : 'bg-red-100 text-red-800'
            }`}>
              {isProfit ? '📈 Profitable' : '📉 Loss'}
            </span>
          </div>
        </div>
      </div>
    </div>
  );
};

export default PortfolioSummaryCard;
