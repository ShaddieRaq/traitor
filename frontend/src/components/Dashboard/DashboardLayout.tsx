import React from 'react';
import { DashboardGrid, GridArea } from './DashboardGrid';
import PortfolioSummaryCard from './PortfolioSummaryCard';
import SystemHealthCard from './SystemHealthCard';
import UnifiedBotsList from './UnifiedBotsList';
import UnifiedStatusBar from './UnifiedStatusBar';
import IntelligenceFrameworkPanel from './IntelligenceFrameworkPanel';
import MarketRegimeIndicator from './MarketRegimeIndicator';
import StickyActivityPanel from '../Trading/StickyActivityPanel';
import { useEnhancedBotsStatus } from '../../hooks/useBots';
import { useMarketRegimeData } from '../../hooks/useMarketRegimeData';

interface DashboardLayoutProps {
  className?: string;
}

/**
 * Main dashboard layout implementing Phase 1 redesign
 * Features:
 * - Responsive grid system (4-column desktop, 2-column tablet, 1-column mobile)
 * - Information hierarchy (Critical, Important, Supporting)
 * - Unified status bar
 * - Grid-based component arrangement
 */
export const DashboardLayout: React.FC<DashboardLayoutProps> = ({ 
  className = '' 
}) => {
  const { data: enhancedBotsStatus } = useEnhancedBotsStatus();
  const { data: marketRegimeData, isLoading: isMarketRegimeLoading, dataUpdatedAt } = useMarketRegimeData();

  return (
    <div className={`min-h-screen bg-gray-50 ${className}`}>
      {/* Unified Status Bar - Always Visible */}
      <UnifiedStatusBar />

      {/* Main Content Area */}
      <div className="p-6">
        {/* Sticky Activity Panel - Keep existing functionality */}
        <div className="mb-6">
          <StickyActivityPanel bots={enhancedBotsStatus || []} />
        </div>

        {/* Market Regime Intelligence Indicator - Phase 5B */}
        <div className="mb-6">
          <MarketRegimeIndicator 
            data={marketRegimeData}
            isLoading={isMarketRegimeLoading}
            dataUpdatedAt={dataUpdatedAt}
          />
        </div>

        {/* Main Dashboard Grid */}
        <DashboardGrid className="mb-6">
          {/* Critical Information - Top Priority */}
          <GridArea area="portfolio">
            <PortfolioSummaryCard />
          </GridArea>

          <GridArea area="systemHealth">
            <SystemHealthCard />
          </GridArea>

          {/* Unified Bots List - Spans full width for comprehensive view */}
          <GridArea area="hotBots" className="col-span-full">
            <UnifiedBotsList />
          </GridArea>
        </DashboardGrid>

        {/* Additional Content Area for Optional Components */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* Intelligence Framework Panel - Phase 5 Addition */}
          <div className="lg:col-span-2">
            <IntelligenceFrameworkPanel />
          </div>
          
          {/* Space for future components */}
          {/* MarketTicker, AutoBotCreator, etc. can go here */}
        </div>
      </div>
    </div>
  );
};

export default DashboardLayout;
