import React, { useState } from 'react';
import PortfolioOverview from '../components/Trading/PortfolioOverview';
import MarketTicker from '../components/Market/MarketTicker';
import MarketAnalysis from '../components/MarketAnalysis';
import AutoBotCreator from '../components/Trading/AutoBotCreator';
import SystemHealthPanel from '../components/Trading/SystemHealthPanel';
import { useBotsStatus, useEnhancedBotsStatus } from '../hooks/useBots';
import { useSystemStatus, getSystemHealthColor, getServiceStatusText } from '../hooks/useSystemStatus';
import { DataFreshnessIndicator, PollingStatusIndicator } from '../components/DataFreshnessIndicators';
import ConsolidatedBotCard from '../components/Trading/ConsolidatedBotCard';
import EnhancedTradingActivitySection from '../components/Trading/EnhancedTradingActivitySection';
import BalanceStatusIndicator from '../components/Trading/BalanceStatusIndicator';
import StickyActivityPanel from '../components/Trading/StickyActivityPanel';
import { TradeExecutionFeed } from '../components/Trading/TradeExecutionFeed';
import { TradeProgressIndicator } from '../components/Trading/TradeProgressIndicator';
import { useTradeExecutionToasts } from '../hooks/useTradeExecutionToasts';

const Dashboard: React.FC = () => {
  const [activeTab, setActiveTab] = useState('overview');
  const { data: botsStatus } = useBotsStatus();
  const { data: enhancedBotsStatus, isLoading, dataUpdatedAt, isFetching } = useEnhancedBotsStatus();
  const { data: systemStatus } = useSystemStatus();
  
  // Real-time trade execution updates
  const { updates: tradeUpdates, isExecuting } = useTradeExecutionToasts();
  
  // Use enhanced data when available, fall back to basic data
  const displayBots = enhancedBotsStatus || botsStatus || [];
  const runningBots = displayBots?.filter(bot => bot.status === 'RUNNING') || [];
  const hotBots = displayBots?.filter(bot => bot.temperature === 'HOT') || [];
  const totalBots = displayBots?.length || 0;

  const tabs = [
    { id: 'overview', name: 'Trading Overview', icon: '📊' },
    { id: 'analysis', name: 'Market Analysis', icon: '🔍' },
  ];
  
  const renderTabContent = () => {
    switch (activeTab) {
      case 'analysis':
        return <MarketAnalysis />;
      case 'overview':
      default:
        return (
          <div className="space-y-6">
            {/* Portfolio Overview - Position Tracking */}
            <PortfolioOverview />

            {/* System Health Panel - Error Tracking */}
            <SystemHealthPanel />

            {/* Auto Bot Creator */}
            <AutoBotCreator />

            {/* Market Ticker */}
            <MarketTicker />

            {/* Trade Execution Progress */}
            {(isExecuting || tradeUpdates.length > 0) && (
              <div className="space-y-4">
                {isExecuting && <TradeProgressIndicator updates={tradeUpdates} isExecuting={isExecuting} />}
                {tradeUpdates.length > 0 && (
                  <TradeExecutionFeed />
                )}
              </div>
            )}

            {/* Real-time Bot Temperature Monitor */}
            <div className="bg-white overflow-hidden shadow rounded-lg">
              <div className="px-4 py-5 sm:p-6">
                <div className="flex items-center justify-between">
                  <div className="flex items-center">
                    <div className="flex-shrink-0">
                      <div className="text-2xl">🌡️</div>
                    </div>
                    <div className="ml-5 flex-1 min-w-0">
                      <dl>
                        <dt className="text-sm font-medium text-gray-500 truncate">
                          Real-time Bot Temperature Monitor
                        </dt>
                        <dd className="mt-1 text-2xl font-semibold text-gray-900 whitespace-nowrap">
                          {totalBots} Bots • {runningBots.length} Running • {hotBots.length} Hot
                        </dd>
                      </dl>
                    </div>
                  </div>
                  
                  {/* System Status Indicators */}
                  <div className="flex flex-col space-y-2">
                    <PollingStatusIndicator isPolling={!isLoading} interval={5000} />
                    <DataFreshnessIndicator 
                      lastUpdated={new Date(dataUpdatedAt)} 
                      showTimestamp={true}
                      freshThresholdSeconds={10}
                      staleThresholdSeconds={30}
                    />
                    {isFetching && (
                      <div className="flex items-center space-x-1">
                        <div className="w-2 h-2 bg-blue-400 rounded-full animate-spin"></div>
                        <span className="text-xs text-gray-500">Updating...</span>
                      </div>
                    )}
                  </div>
                </div>
                
                {/* Bot Status Cards */}
                <div className="mt-6 space-y-4">
                  {enhancedBotsStatus?.map((bot) => (
                    <ConsolidatedBotCard 
                      key={`consolidated-bot-${bot.id}-${bot.current_combined_score}`}
                      bot={bot}
                    />
                  )) || displayBots?.map((bot) => (
                    <div key={`bot-${bot.id}-${bot.current_combined_score}`} className="p-4 bg-gray-50 rounded-lg border-2 border-gray-200">
                      <div className="flex items-center justify-between">
                        <div>
                          <div className="flex items-center space-x-2">
                            <h4 className="text-sm font-medium text-gray-900">{bot.name}</h4>
                            <DataFreshnessIndicator 
                              lastUpdated={new Date(dataUpdatedAt)} 
                              size="sm"
                              freshThresholdSeconds={10}
                              staleThresholdSeconds={30}
                            />
                          </div>
                          <p className="text-xs text-gray-500">{bot.pair}</p>
                        </div>
                        <div className="flex items-center space-x-2">
                          <span className={`text-xs px-2 py-1 rounded ${bot.status === 'RUNNING' ? 'bg-green-100 text-green-800' : 'bg-gray-100 text-gray-600'}`}>
                            {bot.status}
                          </span>
                          <div className="flex items-center space-x-1">
                            <span className="text-2xl">
                              {bot.temperature === 'HOT' ? '🔥' : bot.temperature === 'WARM' ? '🌡️' : bot.temperature === 'COOL' ? '❄️' : '🧊'}
                            </span>
                            {isFetching && (
                              <div className="w-1 h-1 bg-blue-400 rounded-full animate-pulse"></div>
                            )}
                          </div>
                        </div>
                      </div>
                      <div className="mt-2">
                        <div className="flex items-center justify-between">
                          <p className="text-sm text-gray-600">
                            Score: <span className="font-mono font-semibold">{bot.current_combined_score.toFixed(3)}</span>
                          </p>
                          <span className="text-xs text-gray-400">
                            {new Date(dataUpdatedAt).toLocaleTimeString()}
                          </span>
                        </div>
                        <p className="text-xs text-gray-500">
                          Temperature: {bot.temperature} • Distance: {bot.distance_to_signal?.toFixed(2) || 'N/A'}
                        </p>
                      </div>
                    </div>
                  )) || (
                    <div className="text-sm text-gray-500">
                      {isLoading ? 'Loading bot data...' : 'No bots found'}
                    </div>
                  )}
                </div>
              </div>
            </div>

            {/* Balance Status */}
            <BalanceStatusIndicator bots={enhancedBotsStatus || []} />

            {/* Enhanced Trading Activity */}
            <EnhancedTradingActivitySection bots={enhancedBotsStatus || []} />
          </div>
        );
    }
  };

  return (
    <div className="space-y-6">
      {/* Sticky Activity Panel */}
      <StickyActivityPanel bots={enhancedBotsStatus || []} />
      
      {/* Global System Status Bar */}
      <div className="bg-blue-50 border border-blue-200 rounded-lg px-4 py-3">
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-4">
            <div className="flex items-center space-x-2">
              <div className="text-sm font-medium text-gray-900">System Status:</div>
              <div className="flex items-center space-x-1">
                <div className={`w-2 h-2 rounded-full ${getSystemHealthColor(systemStatus)}`}></div>
                <span className={`text-sm ${systemStatus?.status === 'healthy' ? 'text-green-700' : systemStatus?.status === 'degraded' ? 'text-yellow-700' : 'text-red-700'}`}>
                  {getServiceStatusText(systemStatus)}
                </span>
              </div>
            </div>
            <div className="text-gray-300">|</div>
            <PollingStatusIndicator isPolling={!isLoading} interval={5000} />
            {systemStatus?.data_freshness?.market_data && (
              <>
                <div className="text-gray-300">|</div>
                <div className="flex items-center space-x-1">
                  <span className="text-xs text-gray-600">Market Data:</span>
                  <div className={`w-2 h-2 rounded-full ${systemStatus.data_freshness.market_data.healthy ? 'bg-green-400' : 'bg-red-400'}`}></div>
                  <span className="text-xs text-gray-500">
                    {systemStatus.data_freshness.market_data.seconds_since_update 
                      ? `${Math.round(systemStatus.data_freshness.market_data.seconds_since_update)}s ago`
                      : 'No data'
                    }
                  </span>
                </div>
              </>
            )}
          </div>
          <div className="flex items-center space-x-4">
            <DataFreshnessIndicator 
              lastUpdated={new Date(dataUpdatedAt)} 
              showTimestamp={true}
              size="sm"
              freshThresholdSeconds={10}
              staleThresholdSeconds={30}
            />
            {isFetching && (
              <div className="flex items-center space-x-1">
                <div className="w-3 h-3 border-2 border-blue-400 border-t-transparent rounded-full animate-spin"></div>
                <span className="text-sm text-blue-600">Refreshing data...</span>
              </div>
            )}
          </div>
        </div>
      </div>

      <div className="md:flex md:items-center md:justify-between">
        <div className="flex-1 min-w-0">
          <h2 className="text-2xl font-bold leading-7 text-gray-900 sm:text-3xl sm:truncate">
            Dashboard
          </h2>
          <p className="mt-1 text-sm text-gray-500">
            Monitor your trading bot performance and market analysis tools
          </p>
        </div>
      </div>

      {/* Tab Navigation */}
      <div className="border-b border-gray-200">
        <nav className="-mb-px flex space-x-8">
          {tabs.map((tab) => (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id)}
              className={`${
                activeTab === tab.id
                  ? 'border-indigo-500 text-indigo-600'
                  : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
              } whitespace-nowrap py-2 px-1 border-b-2 font-medium text-sm flex items-center space-x-2`}
            >
              <span>{tab.icon}</span>
              <span>{tab.name}</span>
            </button>
          ))}
        </nav>
      </div>

      {/* Tab Content */}
      {renderTabContent()}
    </div>
  );
};

export default Dashboard;
