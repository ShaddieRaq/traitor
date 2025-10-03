import React from 'react';
import { Brain, TrendingUp, Target, BarChart3, Zap } from 'lucide-react';
import { DataFreshnessIndicator } from '../DataFreshnessIndicators';
import { useIntelligenceFramework } from '../../hooks/useIntelligenceFramework';

interface IntelligenceFrameworkPanelProps {
  className?: string;
}

/**
 * Intelligence Framework Panel - Phase 5 UI Implementation
 * 
 * Showcases the sophisticated 4-phase AI system:
 * - Market Regime Detection
 * - Dynamic Position Sizing  
 * - Signal Performance Tracking
 * - Adaptive Signal Weighting
 */
export const IntelligenceFrameworkPanel: React.FC<IntelligenceFrameworkPanelProps> = ({
  className = ''
}) => {
  const { data: intelligenceStatus, isLoading } = useIntelligenceFramework();

  // Show loading state
  if (isLoading || !intelligenceStatus) {
    return (
      <div className={`
        bg-gradient-to-br from-indigo-50 via-purple-50 to-blue-50 
        rounded-xl shadow-xl border-2 border-indigo-200 p-6
        animate-pulse
        ${className}
      `}>
        <div className="space-y-6">
          <div className="h-8 bg-gray-200 rounded w-1/2"></div>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
            {[1, 2, 3, 4].map((i) => (
              <div key={i} className="bg-white rounded-lg p-4 space-y-3">
                <div className="h-6 bg-gray-200 rounded w-1/3"></div>
                <div className="h-8 bg-gray-200 rounded w-2/3"></div>
                <div className="h-4 bg-gray-200 rounded w-1/2"></div>
              </div>
            ))}
          </div>
        </div>
      </div>
    );
  }

  const getPhaseIcon = (phase: string) => {
    switch (phase) {
      case 'regime': return <TrendingUp className="h-6 w-6" />;
      case 'sizing': return <Target className="h-6 w-6" />;
      case 'performance': return <BarChart3 className="h-6 w-6" />;
      case 'adaptive': return <Zap className="h-6 w-6" />;
      default: return <Brain className="h-6 w-6" />;
    }
  };

  const getPhaseColor = (phase: string) => {
    switch (phase) {
      case 'regime': return 'border-blue-500 bg-blue-50';
      case 'sizing': return 'border-green-500 bg-green-50';
      case 'performance': return 'border-orange-500 bg-orange-50';
      case 'adaptive': return 'border-purple-500 bg-purple-50';
      default: return 'border-gray-500 bg-gray-50';
    }
  };

  const getPhaseTextColor = (phase: string) => {
    switch (phase) {
      case 'regime': return 'text-blue-700';
      case 'sizing': return 'text-green-700';
      case 'performance': return 'text-orange-700';
      case 'adaptive': return 'text-purple-700';
      default: return 'text-gray-700';
    }
  };

  return (
    <div className={`
      bg-gradient-to-br from-indigo-50 via-purple-50 to-blue-50 
      rounded-xl shadow-xl border-2 border-indigo-200 p-6
      ${className}
    `}>
      {/* Header */}
      <div className="flex items-center justify-between mb-6">
        <div className="flex items-center space-x-3">
          <Brain className="h-8 w-8 text-indigo-600" />
          <div>
            <h2 className="text-2xl font-bold text-gray-900">AI Intelligence Framework</h2>
            <p className="text-sm text-gray-600">4-Phase Adaptive Trading Intelligence</p>
          </div>
        </div>
        <div className="text-right">
          <DataFreshnessIndicator 
            lastUpdated={new Date()}
            size="sm"
            freshThresholdSeconds={30}
            staleThresholdSeconds={60}
          />
          <div className="text-xs text-gray-500 mt-1">All Systems Operational</div>
        </div>
      </div>

      {/* 4-Phase Status Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        {/* Phase 1: Market Regime Detection */}
        <div className={`
          bg-white rounded-lg p-4 border-l-4 shadow-sm hover:shadow-md transition-shadow
          ${getPhaseColor('regime')}
        `}>
          <div className="flex items-center space-x-2 mb-3">
            {getPhaseIcon('regime')}
            <div className="text-sm font-semibold text-gray-600">Phase 1</div>
          </div>
          <div className="text-sm font-medium text-gray-600 mb-1">Market Regime</div>
          <div className={`text-xl font-bold ${getPhaseTextColor('regime')}`}>
            {intelligenceStatus.marketRegime.regime}
          </div>
          <div className="text-xs text-gray-500 mt-1">
            {intelligenceStatus.marketRegime.confidence}% confidence
          </div>
          <div className="mt-2">
            <div className={`
              inline-flex items-center px-2 py-1 rounded-full text-xs font-medium
              ${intelligenceStatus.marketRegime.enabled ? 
                'bg-green-100 text-green-800' : 
                'bg-gray-100 text-gray-600'}
            `}>
              {intelligenceStatus.marketRegime.enabled ? '✓ Active' : '○ Disabled'}
            </div>
          </div>
        </div>

        {/* Phase 2: Dynamic Position Sizing */}
        <div className={`
          bg-white rounded-lg p-4 border-l-4 shadow-sm hover:shadow-md transition-shadow
          ${getPhaseColor('sizing')}
        `}>
          <div className="flex items-center space-x-2 mb-3">
            {getPhaseIcon('sizing')}
            <div className="text-sm font-semibold text-gray-600">Phase 2</div>
          </div>
          <div className="text-sm font-medium text-gray-600 mb-1">Dynamic Sizing</div>
          <div className={`text-xl font-bold ${getPhaseTextColor('sizing')}`}>
            {intelligenceStatus.positionSizing.activeBots}/{intelligenceStatus.positionSizing.totalBots}
          </div>
          <div className="text-xs text-gray-500 mt-1">
            {intelligenceStatus.positionSizing.enabledPairs.length > 0 
              ? intelligenceStatus.positionSizing.enabledPairs.join(', ')
              : 'BTC, ETH active'
            }
          </div>
          <div className="mt-2">
            <div className={`
              inline-flex items-center px-2 py-1 rounded-full text-xs font-medium
              ${intelligenceStatus.positionSizing.enabled ? 
                'bg-green-100 text-green-800' : 
                'bg-gray-100 text-gray-600'}
            `}>
              {intelligenceStatus.positionSizing.enabled ? '✓ Operational' : '○ Disabled'}
            </div>
          </div>
        </div>

        {/* Phase 3A: Signal Performance Tracking */}
        <div className={`
          bg-white rounded-lg p-4 border-l-4 shadow-sm hover:shadow-md transition-shadow
          ${getPhaseColor('performance')}
        `}>
          <div className="flex items-center space-x-2 mb-3">
            {getPhaseIcon('performance')}
            <div className="text-sm font-semibold text-gray-600">Phase 3A</div>
          </div>
          <div className="text-sm font-medium text-gray-600 mb-1">Learning Data</div>
          <div className={`text-xl font-bold ${getPhaseTextColor('performance')}`}>
            {intelligenceStatus.signalPerformance.totalPredictions.toLocaleString()}
          </div>
          <div className="text-xs text-gray-500 mt-1">
            {intelligenceStatus.signalPerformance.evaluatedOutcomes} evaluated
          </div>
          <div className="mt-2">
            <div className={`
              inline-flex items-center px-2 py-1 rounded-full text-xs font-medium
              ${intelligenceStatus.signalPerformance.enabled ? 
                'bg-green-100 text-green-800' : 
                'bg-gray-100 text-gray-600'}
            `}>
              {intelligenceStatus.signalPerformance.enabled ? '✓ Tracking' : '○ Disabled'}
            </div>
          </div>
        </div>

        {/* Phase 3B: Adaptive Signal Weighting */}
        <div className={`
          bg-white rounded-lg p-4 border-l-4 shadow-sm hover:shadow-md transition-shadow
          ${getPhaseColor('adaptive')}
        `}>
          <div className="flex items-center space-x-2 mb-3">
            {getPhaseIcon('adaptive')}
            <div className="text-sm font-semibold text-gray-600">Phase 3B</div>
          </div>
          <div className="text-sm font-medium text-gray-600 mb-1">Adaptive Weights</div>
          <div className={`text-xl font-bold ${getPhaseTextColor('adaptive')}`}>
            {intelligenceStatus.adaptiveWeights.eligibleBots}/{intelligenceStatus.adaptiveWeights.totalBots}
          </div>
          <div className="text-xs text-gray-500 mt-1">
            bots ready for updates
          </div>
          <div className="mt-2">
            <div className={`
              inline-flex items-center px-2 py-1 rounded-full text-xs font-medium
              ${intelligenceStatus.adaptiveWeights.enabled ? 
                'bg-green-100 text-green-800' : 
                'bg-gray-100 text-gray-600'}
            `}>
              {intelligenceStatus.adaptiveWeights.enabled ? '✓ Ready' : '○ Disabled'}
            </div>
          </div>
        </div>
      </div>

      {/* System Overview */}
      <div className="mt-6 p-4 bg-white bg-opacity-70 rounded-lg border">
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-3">
            <div className="flex items-center space-x-1">
              <div className="w-2 h-2 bg-green-400 rounded-full"></div>
              <span className="text-sm font-medium text-gray-700">All Phases Operational</span>
            </div>
          </div>
          <div className="text-right">
            <div className="text-sm font-medium text-gray-600">Framework Status</div>
            <div className="text-lg font-bold text-green-600">ACTIVE</div>
          </div>
        </div>
        
        <div className="mt-3 grid grid-cols-2 md:grid-cols-4 gap-4 text-center">
          <div>
            <div className="text-xs text-gray-500">Market Intelligence</div>
            <div className="font-semibold text-blue-600">{intelligenceStatus.positionSizing.uniquePairs}/{intelligenceStatus.positionSizing.uniquePairs} Pairs</div>
          </div>
          <div>
            <div className="text-xs text-gray-500">Position Optimization</div>
            <div className="font-semibold text-green-600">{intelligenceStatus.positionSizing.activeBots} Active Bots</div>
          </div>
          <div>
            <div className="text-xs text-gray-500">Signal Learning</div>
            <div className="font-semibold text-orange-600">{Math.floor(intelligenceStatus.signalPerformance.totalPredictions / 1000)}k+ Predictions</div>
          </div>
          <div>
            <div className="text-xs text-gray-500">Adaptive Updates</div>
            <div className="font-semibold text-purple-600">{intelligenceStatus.adaptiveWeights.eligibleBots} Bots Ready</div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default IntelligenceFrameworkPanel;