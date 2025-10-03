import React, { useState } from 'react';
import DashboardLayout from '../components/Dashboard/DashboardLayout';
import MarketAnalysis from '../components/MarketAnalysis';
import { TradeProgressIndicator } from '../components/Trading/TradeProgressIndicator';
import { useTradeExecutionToasts } from '../hooks/useTradeExecutionToasts';
import NotificationBell from '../components/Notifications/NotificationBell';
import NotificationPanel from '../components/Notifications/NotificationPanel';
import IntelligenceAnalytics from '../components/IntelligenceAnalytics';

const Dashboard: React.FC = () => {
  const [activeTab, setActiveTab] = useState('overview');
  
  // Real-time trade execution updates
  const { updates: tradeUpdates, isExecuting } = useTradeExecutionToasts();

  const tabs = [
    { id: 'overview', name: 'Trading Overview', icon: '📊' },
    { id: 'analysis', name: 'Market Analysis', icon: '🔍' },
    { id: 'intelligence', name: 'AI Intelligence', icon: '🤖' },
    { id: 'notifications', name: 'Notifications', icon: '🔔' },
  ];
  
  const renderTabContent = () => {
    switch (activeTab) {
      case 'analysis':
        return <MarketAnalysis />;
      case 'intelligence':
        return <IntelligenceAnalytics />;
      case 'notifications':
        return <NotificationPanel />;
      case 'overview':
      default:
        return (
          <div className="space-y-6">
            {/* Phase 1 Redesigned Dashboard */}
            <DashboardLayout />

            {/* Trade Execution Progress - Live status only */}
            {isExecuting && (
              <div className="max-w-7xl mx-auto px-4 mb-6">
                <TradeProgressIndicator updates={tradeUpdates} isExecuting={isExecuting} />
              </div>
            )}
          </div>
        );
    }
  };

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Page Header */}
      <div className="bg-white shadow">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center py-6">
            <div>
              <h1 className="text-3xl font-bold text-gray-900">
                Trading Dashboard
              </h1>
              <p className="mt-1 text-sm text-gray-600">
                Monitor your trading bot performance and market analysis
              </p>
            </div>
            
            {/* Notification Bell */}
            <div className="flex items-center space-x-4">
              <NotificationBell />
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
        </div>
      </div>

      {/* Tab Content */}
      <div className="py-6">
        {renderTabContent()}
      </div>
    </div>
  );
};

export default Dashboard;
