import React from 'react';
import { DashboardGrid, GridArea } from './DashboardGrid';
import PortfolioSummaryCard from './PortfolioSummaryCard';
import SystemHealthCard from './SystemHealthCard';
import HotBotsSection from './HotBotsSection';
import BotGridSection from './BotGridSection';
import UnifiedStatusBar from './UnifiedStatusBar';
import StickyActivityPanel from '../Trading/StickyActivityPanel';
import { useEnhancedBotsStatus } from '../../hooks/useBots';

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

        {/* Main Dashboard Grid */}
        <DashboardGrid className="mb-6">
          {/* Critical Information - Top Priority */}
          <GridArea area="portfolio">
            <PortfolioSummaryCard />
          </GridArea>

          <GridArea area="systemHealth">
            <SystemHealthCard />
          </GridArea>

          {/* Important Information - High Visibility */}
          <GridArea area="hotBots">
            <HotBotsSection />
          </GridArea>

          {/* Supporting Information - Detailed View */}
          <GridArea area="allBots">
            <BotGridSection />
          </GridArea>
        </DashboardGrid>

        {/* Additional Content Area for Optional Components */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* Space for future Phase 2 components */}
          {/* MarketTicker, AutoBotCreator, etc. can go here */}
        </div>
      </div>
    </div>
  );
};

export default DashboardLayout;
