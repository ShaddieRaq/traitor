import React, { useState } from 'react';
import { DashboardGrid, GridArea } from './DashboardGrid';
import PortfolioSummaryCard from './PortfolioSummaryCard';
import SystemHealthCard from './SystemHealthCard';
import TieredBotsView from './TieredBotsView';
import UnifiedStatusBar from './UnifiedStatusBar';
import StickyActivityPanel from '../Trading/StickyActivityPanel';
import IntelligenceFrameworkPanel from './IntelligenceFrameworkPanel';
import { useEnhancedBotsStatus } from '../../hooks/useBots';
import { Eye, EyeOff } from 'lucide-react';

interface DashboardLayoutProps {
  className?: string;
}

/**
 * Intelligent trading dashboard - combines financial data with smart UX
 * Principles:
 * 1. Show critical financial data first (portfolio, system health)
 * 2. Smart activity monitoring (only show when relevant) 
 * 3. Actionable bot grouping (problems first, opportunities second)
 * 4. Progressive disclosure with smart defaults
 */
export const DashboardLayout: React.FC<DashboardLayoutProps> = ({ 
  className = '' 
}) => {
  const [isFocusMode, setIsFocusMode] = useState(false);
  const { data: enhancedBotsStatus } = useEnhancedBotsStatus();

  // Show ALL bots - no filtering
  const botsToShow = enhancedBotsStatus || [];

  return (
    <div className={`min-h-screen bg-gradient-to-br from-gray-50 to-gray-100 ${className}`}>
      {/* Status Bar */}
      <UnifiedStatusBar />

      {/* Smart Activity Panel - Only show when there's actual activity */}
      {enhancedBotsStatus && enhancedBotsStatus.some(bot => 
        bot.confirmation?.is_active || bot.trade_readiness?.can_trade
      ) && (
        <StickyActivityPanel bots={enhancedBotsStatus} />
      )}

      {/* Main Content */}
      <div className="max-w-7xl mx-auto p-4 sm:p-6 lg:p-8 space-y-6">
        
        {/* Header with Controls */}
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-2xl font-bold text-gray-900">Trading Dashboard</h1>
            <p className="text-gray-600 text-sm mt-1">
              Showing all {enhancedBotsStatus?.length || 0} bots
            </p>
          </div>
          
          <div className="flex items-center space-x-3">
            {/* Focus Mode */}
            <button
              onClick={() => setIsFocusMode(!isFocusMode)}
              className={`
                flex items-center space-x-2 px-3 py-2 rounded-lg transition-all duration-200 text-sm
                ${isFocusMode 
                  ? 'bg-orange-100 text-orange-700 ring-1 ring-orange-200' 
                  : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
                }
              `}
            >
              {isFocusMode ? (
                <>
                  <EyeOff className="w-4 h-4" />
                  <span>Focus Mode</span>
                </>
              ) : (
                <>
                  <Eye className="w-4 h-4" />
                  <span>Focus</span>
                </>
              )}
            </button>
          </div>
        </div>

        {/* Critical Financial Data Grid */}
        <DashboardGrid className="mb-6">
          <GridArea area="portfolio">
            <PortfolioSummaryCard />
          </GridArea>
          
          <GridArea area="systemHealth">
            <SystemHealthCard />
          </GridArea>
        </DashboardGrid>

        {/* Bot Management with Smart Defaults */}
        <div className="space-y-4">
          <div className="flex items-center justify-between">
            <div>
              <h2 className="text-lg font-semibold text-gray-900">Trading Bots</h2>
              <p className="text-sm text-gray-600">
                Showing all active trading bots
              </p>
            </div>
          </div>
          
          {/* Pass filtered bots to the tiered view */}
          <TieredBotsView botsData={botsToShow} />
        </div>

        {/* Advanced Features - Collapsed in Focus Mode */}
        {!isFocusMode && (
          <div className="border-t pt-6 mt-8">
            <h2 className="text-lg font-semibold text-gray-900 mb-4">
              AI Intelligence Framework
            </h2>
            <IntelligenceFrameworkPanel />
          </div>
        )}
      </div>
    </div>
  );
};

export default DashboardLayout;