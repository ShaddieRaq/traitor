import React, { useState } from 'react';
import { DashboardGrid, GridArea } from './DashboardGrid';
import PortfolioSummaryCard from './PortfolioSummaryCard';
import SystemHealthCard from './SystemHealthCard';
import TieredBotsView from './TieredBotsView';
import UnifiedStatusBar from './UnifiedStatusBar';
import StickyActivityPanel from '../Trading/StickyActivityPanel';
import BotForm from '../BotForm';
import SystemDiagnosticsModal from './SystemDiagnosticsModal';
import { useEnhancedBotsStatus, useCreateBot, useUpdateBot } from '../../hooks/useBots';
import { Eye, EyeOff, Plus, Brain } from 'lucide-react';
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
  const [isFocusMode, setIsFocusMode] = useState(false);
  const [showBotForm, setShowBotForm] = useState(false);
  const [editingBot, setEditingBot] = useState<Bot | null>(null);
  const [showDiagnostics, setShowDiagnostics] = useState(false);
  
  const { data: enhancedBotsStatus } = useEnhancedBotsStatus();
  const createBot = useCreateBot();
  const updateBot = useUpdateBot();

  // Show ALL bots - no filtering
  const botsToShow = enhancedBotsStatus || [];

  const handleCreateBot = () => {
    setEditingBot(null);
    setShowBotForm(true);
  };

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
            {/* Create Bot Button */}
            <button
              onClick={handleCreateBot}
              className="flex items-center space-x-2 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors text-sm font-medium"
            >
              <Plus className="w-4 h-4" />
              <span>Create Bot</span>
            </button>
            
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
                    <p className="text-xs text-gray-600">141K+ predictions • 63.3% accuracy</p>
                  </div>
                </div>
                <div className="flex items-center space-x-6">
                  <div className="text-center">
                    <div className="text-sm font-bold text-green-600">✓ TRENDING</div>
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

        {/* Bot Management with Smart Defaults */}
        <div className="space-y-4">
          <div className="flex items-center justify-between">
            <div>
              <h2 className="text-lg font-semibold text-gray-900">Trading Bots</h2>
              <p className="text-sm text-gray-600">
                Organized by signal strength and trading activity
              </p>
            </div>
          </div>
          
          <TieredBotsView 
            botsData={botsToShow} 
            onEditBot={handleEditBot}
          />
        </div>
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