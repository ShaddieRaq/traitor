import React from 'react';
import { AlertTriangle, DollarSign, Activity, CheckCircle } from 'lucide-react';
import { useEnhancedBotsStatus } from '../../hooks/useBots';

interface ExecutiveSummaryProps {
  className?: string;
}

/**
 * Executive Summary - Shows only what executives/traders need to know at a glance
 * Follows the "inverted pyramid" journalism principle: most important info first
 */
export const ExecutiveSummary: React.FC<ExecutiveSummaryProps> = ({ 
  className = '' 
}) => {
  const { data: botsData } = useEnhancedBotsStatus();

  if (!botsData) {
    return (
      <div className={`bg-white rounded-lg border p-6 ${className}`}>
        <div className="animate-pulse space-y-4">
          <div className="h-8 bg-gray-200 rounded w-1/3"></div>
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
            {[1, 2, 3, 4].map(i => (
              <div key={i} className="space-y-3">
                <div className="h-12 bg-gray-200 rounded"></div>
                <div className="h-4 bg-gray-200 rounded w-2/3"></div>
              </div>
            ))}
          </div>
        </div>
      </div>
    );
  }

  // Calculate critical metrics
  const totalBots = botsData.length;
  const activeBots = botsData.filter(bot => bot.status === 'RUNNING').length;
  const alertCount = botsData.filter(bot => 
    bot.trade_readiness?.status === 'blocked' || 
    bot.temperature === 'HOT'
  ).length;
  
  // Calculate total portfolio value (simplified)
  const totalPositionValue = botsData.reduce((sum, bot) => {
    if (bot.last_trade?.price && bot.current_position_size) {
      return sum + (Math.abs(bot.current_position_size) * bot.last_trade.price);
    }
    return sum;
  }, 0);

  const profitableBots = botsData.filter(bot => 
    bot.current_position_size && bot.current_position_size > 0
  ).length;

  return (
    <div className={`bg-white rounded-xl shadow-sm border p-6 ${className}`}>
      {/* Header */}
      <div className="flex items-center justify-between mb-6">
        <h1 className="text-2xl font-bold text-gray-900">
          Trading Overview
        </h1>
        <div className="flex items-center space-x-2 text-sm text-gray-500">
          <Activity className="w-4 h-4" />
          <span>Live</span>
        </div>
      </div>

      {/* Critical Metrics - Large, scannable */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-6 mb-6">
        {/* Portfolio Value */}
        <div className="text-center">
          <div className="flex items-center justify-center w-12 h-12 bg-green-100 rounded-lg mx-auto mb-3">
            <DollarSign className="w-6 h-6 text-green-600" />
          </div>
          <div className="text-3xl font-bold text-gray-900">
            ${totalPositionValue.toFixed(0)}
          </div>
          <div className="text-sm text-gray-500">Portfolio Value</div>
        </div>

        {/* Alerts */}
        <div className="text-center">
          <div className={`flex items-center justify-center w-12 h-12 rounded-lg mx-auto mb-3 ${
            alertCount > 0 ? 'bg-red-100' : 'bg-gray-100'
          }`}>
            <AlertTriangle className={`w-6 h-6 ${
              alertCount > 0 ? 'text-red-600' : 'text-gray-400'
            }`} />
          </div>
          <div className={`text-3xl font-bold ${
            alertCount > 0 ? 'text-red-600' : 'text-gray-900'
          }`}>
            {alertCount}
          </div>
          <div className="text-sm text-gray-500">Alerts</div>
        </div>

        {/* Active Bots */}
        <div className="text-center">
          <div className="flex items-center justify-center w-12 h-12 bg-blue-100 rounded-lg mx-auto mb-3">
            <Activity className="w-6 h-6 text-blue-600" />
          </div>
          <div className="text-3xl font-bold text-gray-900">
            {activeBots}/{totalBots}
          </div>
          <div className="text-sm text-gray-500">Active Bots</div>
        </div>

        {/* Profitable Positions */}
        <div className="text-center">
          <div className="flex items-center justify-center w-12 h-12 bg-green-100 rounded-lg mx-auto mb-3">
            <CheckCircle className="w-6 h-6 text-green-600" />
          </div>
          <div className="text-3xl font-bold text-green-600">
            {profitableBots}
          </div>
          <div className="text-sm text-gray-500">Profitable</div>
        </div>
      </div>

      {/* Quick Actions - Only if there are actionable items */}
      {alertCount > 0 && (
        <div className="border-t pt-4">
          <div className="flex items-center justify-between">
            <div className="text-sm font-medium text-gray-700">
              {alertCount} {alertCount === 1 ? 'bot needs' : 'bots need'} attention
            </div>
            <button className="px-4 py-2 bg-red-50 text-red-700 rounded-lg hover:bg-red-100 transition-colors text-sm font-medium">
              View Alerts
            </button>
          </div>
        </div>
      )}
    </div>
  );
};

export default ExecutiveSummary;