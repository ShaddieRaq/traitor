import React, { useState } from 'react';
import { DashboardGrid, GridArea } from './DashboardGrid';
import PortfolioSummaryCard from './PortfolioSummaryCard';
import SystemHealthCard from './SystemHealthCard';
import { DualViewBotsDisplay } from './DualViewBotsDisplay';
import UnifiedStatusBar from './UnifiedStatusBar';
import BotForm from '../BotForm';
import SystemDiagnosticsModal from './SystemDiagnosticsModal';
import { useEnhancedBotsStatus, useCreateBot, useUpdateBot } from '../../hooks/useBots';
import { useBitcoinTrend, getTrendDirection, getRegimeDisplay } from '../../hooks/useTrends';
import { useIntelligenceFramework } from '../../hooks/useIntelligenceFramework';
import { Brain } from 'lucide-react';
import { Bot, BotCreate, BotUpdate } from '../../types';
import toast from 'react-hot-toast';

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
  const [showBotForm, setShowBotForm] = useState(false);
  const [editingBot, setEditingBot] = useState<Bot | null>(null);
  const [showDiagnostics, setShowDiagnostics] = useState(false);
  
  const { data: enhancedBotsStatus } = useEnhancedBotsStatus();
  const { data: bitcoinTrend, isLoading: trendLoading } = useBitcoinTrend();
  const { data: intelligenceData } = useIntelligenceFramework();
  const createBot = useCreateBot();
  const updateBot = useUpdateBot();

  // Show ALL bots - no filtering
  const botsToShow = enhancedBotsStatus || [];

  const handleEditBot = (bot: Bot) => {
    setEditingBot(bot);
    setShowBotForm(true);
  };

  const handleFormSubmit = (data: BotCreate) => {
    if (editingBot) {
      // Convert BotCreate to BotUpdate format
      const updateData: BotUpdate = {
        name: data.name,
        position_size_usd: data.position_size_usd,
        max_positions: data.max_positions,
        stop_loss_pct: data.stop_loss_pct,
        take_profit_pct: data.take_profit_pct,
        trade_step_pct: data.trade_step_pct,
        cooldown_minutes: data.cooldown_minutes,
        signal_config: data.signal_config
      };
      
      updateBot.mutate(
        { id: editingBot.id, bot: updateData },
        {
          onSuccess: () => {
            setShowBotForm(false);
            setEditingBot(null);
            toast.success(`Bot "${data.name}" updated successfully`);
          },
          onError: () => {
            toast.error(`Failed to update bot "${data.name}"`);
          }
        }
      );
    } else {
      // Create new bot
      createBot.mutate(data, {
        onSuccess: () => {
          setShowBotForm(false);
          toast.success(`Bot "${data.name}" created successfully`);
        },
        onError: () => {
          toast.error(`Failed to create bot "${data.name}"`);
        }
      });
    }
  };

  const handleFormCancel = () => {
    setShowBotForm(false);
    setEditingBot(null);
  };

  return (
    <div className={`min-h-screen bg-gradient-to-br from-gray-50 to-gray-100 ${className}`}>
      {/* Status Bar */}
      <UnifiedStatusBar />

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
        </div>

        {/* Critical Financial Data Grid */}
        <DashboardGrid className="mb-6">
          <GridArea area="portfolio">
            <PortfolioSummaryCard />
          </GridArea>
          
          <GridArea area="systemHealth">
            <SystemHealthCard onViewDetails={() => setShowDiagnostics(true)} />
          </GridArea>
          
          {/* AI Intelligence Framework - Integrated in Grid */}
          <GridArea area="intelligence">
            <div className="bg-gradient-to-r from-purple-50 to-indigo-50 rounded-lg border border-purple-200 p-4 h-full">
              <div className="flex items-center justify-between h-full">
                <div className="flex items-center space-x-3">
                  <div className="p-2 bg-purple-100 rounded-lg">
                    <Brain className="h-5 w-5 text-purple-600" />
                  </div>
                  <div>
                    <h3 className="text-lg font-semibold text-gray-900">AI Intelligence</h3>
                    <p className="text-xs text-gray-600">
                      {intelligenceData?.profitMetrics ? (
                        `$${(intelligenceData.profitMetrics.totalProfit || 0).toFixed(2)} total profit • ${intelligenceData?.topPerformers?.winners?.length || 0} winners identified • ${intelligenceData?.topPerformers?.losers?.length || 0} losers to pause`
                      ) : (
                        "Loading profit analysis..."
                      )}
                    </p>
                  </div>
                </div>
                <div className="flex items-center space-x-6">
                  <div className="text-center">
                    {!trendLoading && bitcoinTrend ? (() => {
                      const direction = getTrendDirection(bitcoinTrend.trend_strength, bitcoinTrend.moving_average_alignment);
                      const regimeDisplay = getRegimeDisplay(bitcoinTrend.regime, direction.direction);
                      return (
                        <div className={`text-sm font-bold ${direction.color}`}>
                          {direction.emoji} {regimeDisplay}
                        </div>
                      );
                    })() : (
                      <div className="text-sm font-bold text-gray-400">
                        ⏳ LOADING...
                      </div>
                    )}
                    <div className="text-xs text-gray-500">Market Regime</div>
                  </div>
                  <div className="text-center">
                    <div className="text-sm font-bold text-blue-600">$36-50</div>
                    <div className="text-xs text-gray-500">Position Size</div>
                  </div>
                  <div className="text-center">
                    <div className="text-sm font-bold text-purple-600">RSI+MACD</div>
                    <div className="text-xs text-gray-500">Active Signals</div>
                  </div>
                </div>
              </div>
            </div>
          </GridArea>
        </DashboardGrid>

        {/* Bot Management - Integrated Header and Controls */}
        <DualViewBotsDisplay 
          botsData={botsToShow} 
          onEditBot={handleEditBot}
          onCreateBot={() => setShowBotForm(true)}
        />
      </div>

      {/* Bot Form Modal */}
      {showBotForm && (
        <BotForm
          bot={editingBot}
          onSubmit={handleFormSubmit}
          onCancel={handleFormCancel}
          isLoading={createBot.isPending || updateBot.isPending}
        />
      )}

      {/* System Diagnostics Modal */}
      <SystemDiagnosticsModal
        isOpen={showDiagnostics}
        onClose={() => setShowDiagnostics(false)}
      />
    </div>
  );
};

export default DashboardLayout;