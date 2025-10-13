import React from 'react';
import { useEnhancedBotsStatus } from '../../hooks/useBots';
import { DollarSign, TrendingUp, Archive, Activity } from 'lucide-react';

interface CapitalData {
  total: number;
  active: number;
  freed: number;
  available: number;
}

/**
 * CapitalEfficiencyCard - Shows capital allocation across bot lifecycle stages
 * 
 * Capital breakdown:
 * - Total: $500 (fixed allocation)
 * - Active: Sum of ACTIVE + CLOSING bots position_size_usd
 * - Freed: Sum of ARCHIVED bots position_size_usd
 * - Available: Total - Active
 */
export const CapitalEfficiencyCard: React.FC = () => {
  const { data: bots } = useEnhancedBotsStatus();
  
  const calculateCapital = (): CapitalData => {
    if (!bots || bots.length === 0) {
      return { total: 500, active: 0, freed: 0, available: 500 };
    }
    
    // Active bots: ACTIVE + CLOSING (still trading or liquidating)
    const activeBots = bots.filter(b => 
      b.lifecycle_stage === 'ACTIVE' || b.lifecycle_stage === 'CLOSING' || !b.lifecycle_stage
    );
    
    // Archived bots: ARCHIVED (capital freed)
    const archivedBots = bots.filter(b => b.lifecycle_stage === 'ARCHIVED');
    
    // Calculate totals
    const active = activeBots.reduce((sum, bot) => sum + (bot.position_size_usd || 0), 0);
    const freed = archivedBots.reduce((sum, bot) => sum + (bot.position_size_usd || 0), 0);
    const total = 500; // Fixed portfolio allocation
    const available = Math.max(0, total - active); // Prevent negative display
    
    return { total, active, freed, available };
  };
  
  const capital = calculateCapital();
  const efficiency = (capital.active / capital.total) * 100;
  
  // Determine efficiency status
  const getEfficiencyStatus = () => {
    if (efficiency >= 80) return { label: 'Excellent', color: 'text-green-600', bgColor: 'bg-green-50' };
    if (efficiency >= 60) return { label: 'Good', color: 'text-blue-600', bgColor: 'bg-blue-50' };
    if (efficiency >= 40) return { label: 'Moderate', color: 'text-yellow-600', bgColor: 'bg-yellow-50' };
    return { label: 'Low', color: 'text-red-600', bgColor: 'bg-red-50' };
  };
  
  const status = getEfficiencyStatus();
  
  return (
    <div className="bg-white rounded-lg shadow p-6">
      {/* Header */}
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center space-x-2">
          <DollarSign className="h-5 w-5 text-green-600" />
          <h3 className="text-lg font-semibold text-gray-900">Capital Efficiency</h3>
        </div>
        <div className={`px-3 py-1 rounded-full text-xs font-medium ${status.bgColor} ${status.color}`}>
          {status.label}
        </div>
      </div>
      
      {/* Progress Bar */}
      <div className="mb-4">
        <div className="flex justify-between text-sm mb-2">
          <span className="text-gray-600">Capital Deployed</span>
          <span className={`font-medium ${status.color}`}>{efficiency.toFixed(1)}%</span>
        </div>
        <div className="w-full bg-gray-200 rounded-full h-3 overflow-hidden">
          <div 
            className="bg-gradient-to-r from-green-500 to-emerald-600 h-3 rounded-full transition-all duration-500 ease-out"
            style={{ width: `${Math.min(efficiency, 100)}%` }}
          />
        </div>
        <div className="flex justify-between text-xs text-gray-500 mt-1">
          <span>0%</span>
          <span>50%</span>
          <span>100%</span>
        </div>
      </div>
      
      {/* Capital Breakdown */}
      <div className="grid grid-cols-3 gap-4">
        {/* Active Capital */}
        <div className="text-center p-3 bg-green-50 rounded-lg border border-green-200">
          <Activity className="h-4 w-4 text-green-600 mx-auto mb-1" />
          <div className="text-2xl font-bold text-green-700">
            ${capital.active.toFixed(0)}
          </div>
          <div className="text-xs text-gray-600 mt-1">Active Trading</div>
        </div>
        
        {/* Freed Capital */}
        <div className="text-center p-3 bg-blue-50 rounded-lg border border-blue-200">
          <Archive className="h-4 w-4 text-blue-600 mx-auto mb-1" />
          <div className="text-2xl font-bold text-blue-700">
            ${capital.freed.toFixed(0)}
          </div>
          <div className="text-xs text-gray-600 mt-1">Freed Capital</div>
        </div>
        
        {/* Available Capital */}
        <div className="text-center p-3 bg-purple-50 rounded-lg border border-purple-200">
          <TrendingUp className="h-4 w-4 text-purple-600 mx-auto mb-1" />
          <div className="text-2xl font-bold text-purple-700">
            ${capital.available.toFixed(0)}
          </div>
          <div className="text-xs text-gray-600 mt-1">Available</div>
        </div>
      </div>
      
      {/* Info Footer */}
      <div className="mt-4 pt-4 border-t border-gray-200">
        <div className="flex items-center justify-between text-sm">
          <span className="text-gray-600">Total Portfolio</span>
          <span className="font-bold text-gray-900">${capital.total.toFixed(0)}</span>
        </div>
        {capital.freed > 0 && (
          <div className="mt-2 text-xs text-blue-600 bg-blue-50 px-3 py-2 rounded">
            💡 ${capital.freed.toFixed(0)} freed from archived bots will be reallocated to new opportunities
          </div>
        )}
      </div>
    </div>
  );
};
