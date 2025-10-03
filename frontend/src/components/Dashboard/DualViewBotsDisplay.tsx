import React, { useState } from 'react';
import { CompactPerformanceCard, AdvancedAnalyticsCard } from './BotCardSamples';
import { useEnhancedBotsStatus, usePnLData, useStartBot, useStopBot, useDeleteBot } from '../../hooks/useBots';
import { Edit3, Play, Pause, Trash2, LayoutGrid, List } from 'lucide-react';
import toast from 'react-hot-toast';

interface DualViewBotsDisplayProps {
  className?: string;
  botsData?: any[];
  showAllMode?: boolean;
  onEditBot?: (bot: any) => void;
}

type ViewMode = 'compact' | 'advanced' | 'smart';

export const DualViewBotsDisplay: React.FC<DualViewBotsDisplayProps> = ({ 
  className = '',
  botsData: propBotsData,
  onEditBot
}) => {
  const { data: hookBotsData } = useEnhancedBotsStatus();
  const { data: pnlData } = usePnLData();
  const [viewMode, setViewMode] = useState<ViewMode>('smart');
  const startBot = useStartBot();
  const stopBot = useStopBot();
  const deleteBot = useDeleteBot();
  
  const botsData = propBotsData || hookBotsData;

  if (!botsData) {
    return <div className={`animate-pulse bg-gray-100 rounded-lg h-64 ${className}`}></div>;
  }

  // Smart view logic: Use advanced cards for HOT/WARM bots, compact for COOL/FROZEN
  const getCardComponent = (bot: any) => {
    if (viewMode === 'compact') return CompactPerformanceCard;
    if (viewMode === 'advanced') return AdvancedAnalyticsCard;
    
    // Smart mode: Advanced for high-priority bots, compact for others
    return (bot.temperature === 'HOT' || bot.temperature === 'WARM') 
      ? AdvancedAnalyticsCard 
      : CompactPerformanceCard;
  };

  // Group bots by temperature
  const groupedBots = {
    HOT: botsData.filter(bot => bot.temperature === 'HOT'),
    WARM: botsData.filter(bot => bot.temperature === 'WARM'),
    COOL: botsData.filter(bot => bot.temperature === 'COOL'),
    FROZEN: botsData.filter(bot => bot.temperature === 'FROZEN')
  };

  const TemperatureGroup = ({ title, icon, bots, bgColor }: { title: string; icon: string; bots: any[]; bgColor: string }) => {
    if (bots.length === 0) return null;
    
    return (
      <div className="border rounded-lg border-gray-200 bg-gray-50 mb-4">
        <div className={`px-4 py-3 border-b border-gray-200 ${bgColor}`}>
          <div className="font-medium text-gray-900 flex items-center justify-between">
            <div className="flex items-center space-x-2">
              <span className="text-xl">{icon}</span>
              <span>{title} ({bots.length})</span>
            </div>
            {/* Show card type indicator for this group */}
            {viewMode === 'smart' && (
              <span className="text-xs text-gray-600 bg-white px-2 py-1 rounded-full">
                {(title === 'HOT BOTS' || title === 'WARM BOTS') ? 'Advanced View' : 'Compact View'}
              </span>
            )}
          </div>
        </div>
        <div className="p-4">
          <div className={`grid gap-4 ${
            // Responsive grid that adapts to card type
            viewMode === 'compact' ? 'grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4' :
            viewMode === 'advanced' ? 'grid-cols-1 lg:grid-cols-2 xl:grid-cols-3' :
            // Smart mode: different grids for different groups
            (title === 'HOT BOTS' || title === 'WARM BOTS') 
              ? 'grid-cols-1 lg:grid-cols-2 xl:grid-cols-3'  // Advanced cards - fewer per row
              : 'grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4'  // Compact cards - more per row
          }`}>
            {bots.map((bot: any) => {
              const CardComponent = getCardComponent(bot);
              return (
                <div key={bot.id} className="relative group">
                  <CardComponent 
                    bot={bot} 
                    pnlData={pnlData}
                  />
                  
                  {/* Floating Action Menu */}
                  <div className="absolute top-2 right-2 opacity-0 group-hover:opacity-100 transition-opacity duration-200">
                    <div className="flex items-center space-x-1 bg-white rounded-lg shadow-lg border p-1">
                      {onEditBot && (
                        <button
                          onClick={() => onEditBot(bot)}
                          className="p-1.5 text-gray-500 hover:text-blue-600 hover:bg-blue-50 rounded-md transition-colors"
                          title="Edit Bot"
                        >
                          <Edit3 className="h-3 w-3" />
                        </button>
                      )}
                      
                      {/* Start/Stop toggle */}
                      {bot.status === 'RUNNING' ? (
                        <button
                          onClick={() => {
                            stopBot.mutate(bot.id, {
                              onSuccess: () => toast.success(`Bot "${bot.pair}" stopped`),
                              onError: () => toast.error(`Failed to stop bot "${bot.pair}"`)
                            });
                          }}
                          className="p-1.5 text-blue-600 hover:text-blue-700 hover:bg-blue-50 rounded-md transition-colors"
                          title="Stop Bot"
                        >
                          <Pause className="h-3 w-3" />
                        </button>
                      ) : (
                        <button
                          onClick={() => {
                            startBot.mutate(bot.id, {
                              onSuccess: () => toast.success(`Bot "${bot.pair}" started`),
                              onError: () => toast.error(`Failed to start bot "${bot.pair}"`)
                            });
                          }}
                          className="p-1.5 text-green-600 hover:text-green-700 hover:bg-green-50 rounded-md transition-colors"
                          title="Start Bot"
                        >
                          <Play className="h-3 w-3" />
                        </button>
                      )}
                      
                      <button
                        onClick={() => {
                          if (confirm(`Are you sure you want to delete bot "${bot.pair}"?`)) {
                            deleteBot.mutate(bot.id, {
                              onSuccess: () => toast.success(`Bot "${bot.pair}" deleted`),
                              onError: () => toast.error(`Failed to delete bot "${bot.pair}"`)
                            });
                          }
                        }}
                        className="p-1.5 text-gray-500 hover:text-red-600 hover:bg-red-50 rounded-md transition-colors"
                        title="Delete Bot"
                      >
                        <Trash2 className="h-3 w-3" />
                      </button>
                    </div>
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      </div>
    );
  };

  return (
    <div className={`space-y-4 ${className}`}>
      {/* View Mode Selector */}
      <div className="flex items-center justify-between bg-white rounded-lg border p-4">
        <div>
          <h3 className="text-lg font-semibold text-gray-900">Bot Display Options</h3>
          <p className="text-sm text-gray-600">
            {viewMode === 'smart' 
              ? 'Smart view: Advanced analytics for active bots (🔥HOT/🌡️WARM), compact performance cards for inactive bots (❄️COOL/🧊FROZEN)'
              : viewMode === 'compact' 
                ? 'Compact performance-focused cards optimized for space efficiency'
                : 'Advanced analytics cards with detailed market intelligence and signal analysis'
            }
          </p>
        </div>
        
        <div className="flex items-center space-x-2">
          <div className="flex bg-gray-100 rounded-lg p-1">
            <button
              onClick={() => setViewMode('compact')}
              className={`flex items-center space-x-2 px-3 py-2 rounded-md text-sm font-medium transition-all ${
                viewMode === 'compact'
                  ? 'bg-white text-blue-600 shadow-sm'
                  : 'text-gray-600 hover:text-gray-900'
              }`}
            >
              <LayoutGrid className="h-4 w-4" />
              <span>Compact</span>
            </button>
            
            <button
              onClick={() => setViewMode('smart')}
              className={`flex items-center space-x-2 px-3 py-2 rounded-md text-sm font-medium transition-all ${
                viewMode === 'smart'
                  ? 'bg-white text-blue-600 shadow-sm'
                  : 'text-gray-600 hover:text-gray-900'
              }`}
            >
              <span className="text-lg">🧠</span>
              <span>Smart</span>
            </button>
            
            <button
              onClick={() => setViewMode('advanced')}
              className={`flex items-center space-x-2 px-3 py-2 rounded-md text-sm font-medium transition-all ${
                viewMode === 'advanced'
                  ? 'bg-white text-blue-600 shadow-sm'
                  : 'text-gray-600 hover:text-gray-900'
              }`}
            >
              <List className="h-4 w-4" />
              <span>Advanced</span>
            </button>
          </div>
        </div>
      </div>

      {/* Bots Display */}
      <TemperatureGroup 
        title="HOT BOTS" 
        icon="🔥" 
        bots={groupedBots.HOT} 
        bgColor="bg-gradient-to-r from-red-50 to-orange-50" 
      />
      <TemperatureGroup 
        title="WARM BOTS" 
        icon="🌡️" 
        bots={groupedBots.WARM} 
        bgColor="bg-gradient-to-r from-orange-50 to-yellow-50" 
      />
      <TemperatureGroup 
        title="COOL BOTS" 
        icon="❄️" 
        bots={groupedBots.COOL} 
        bgColor="bg-gradient-to-r from-blue-50 to-cyan-50" 
      />
      <TemperatureGroup 
        title="FROZEN BOTS" 
        icon="🧊" 
        bots={groupedBots.FROZEN} 
        bgColor="bg-gradient-to-r from-gray-50 to-slate-50" 
      />
    </div>
  );
};

export default DualViewBotsDisplay;