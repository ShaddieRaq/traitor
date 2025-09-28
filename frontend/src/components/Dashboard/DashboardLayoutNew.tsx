import React, { useState } from 'react';
import ExecutiveSummary from './ExecutiveSummary';
import TieredBotsView from './TieredBotsView';
import UnifiedStatusBar from './UnifiedStatusBar';
import IntelligenceFrameworkPanel from './IntelligenceFrameworkPanel';
import { Eye, EyeOff } from 'lucide-react';

interface DashboardLayoutProps {
  className?: string;
}

/**
 * Redesigned dashboard with proper UX hierarchy:
 * 1. Executive Summary (what matters most)
 * 2. Tiered Bot View (progressive disclosure) 
 * 3. Advanced features (collapsed by default)
 */
export const DashboardLayout: React.FC<DashboardLayoutProps> = ({ 
  className = '' 
}) => {
  const [isFocusMode, setIsFocusMode] = useState(false);

  return (
    <div className={`min-h-screen bg-gradient-to-br from-gray-50 to-gray-100 ${className}`}>
      {/* Status Bar - Keep for system status */}
      <UnifiedStatusBar />

      {/* Main Content */}
      <div className="max-w-7xl mx-auto p-4 sm:p-6 lg:p-8 space-y-8">
        
        {/* Header with Focus Toggle */}
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-3xl font-bold text-gray-900">Trading Dashboard</h1>
            <p className="text-gray-600 mt-1">Monitor and manage your automated trading system</p>
          </div>
          
          <button
            onClick={() => setIsFocusMode(!isFocusMode)}
            className={`
              flex items-center space-x-2 px-4 py-2 rounded-lg transition-all duration-200
              ${isFocusMode 
                ? 'bg-orange-100 text-orange-700 ring-2 ring-orange-200' 
                : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
              }
            `}
            title={isFocusMode ? 'Show advanced features' : 'Hide advanced features'}
          >
            {isFocusMode ? (
              <>
                <EyeOff className="w-4 h-4" />
                <span className="text-sm font-medium">Focus Mode</span>
              </>
            ) : (
              <>
                <Eye className="w-4 h-4" />
                <span className="text-sm font-medium">Focus</span>
              </>
            )}
          </button>
        </div>

        {/* Executive Summary - Always Visible */}
        <ExecutiveSummary />

        {/* Bot Management - Progressive Disclosure */}
        <div className="space-y-6">
          <div>
            <h2 className="text-xl font-semibold text-gray-900">Trading Bots</h2>
            <p className="text-gray-600 text-sm mt-1">
              Organized by priority - critical issues first, opportunities second
            </p>
          </div>
          <TieredBotsView />
        </div>

        {/* Advanced Features - Hidden in Focus Mode */}
        {!isFocusMode && (
          <div className="space-y-6">
            <div className="border-t pt-8">
              <h2 className="text-xl font-semibold text-gray-900 mb-6">
                Advanced Analytics
              </h2>
              <IntelligenceFrameworkPanel />
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default DashboardLayout;