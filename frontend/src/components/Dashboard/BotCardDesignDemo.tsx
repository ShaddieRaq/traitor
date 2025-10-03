import React, { useState } from 'react';
import { 
  CompactPerformanceCard, 
  AdvancedAnalyticsCard, 
  MinimalModernCard, 
  MetricDenseCard 
} from './BotCardSamples';
import { useEnhancedBotsStatus, usePnLData } from '../../hooks/useBots';

// Demo page to showcase different bot card designs
export const BotCardDesignDemo: React.FC = () => {
  const { data: botsData } = useEnhancedBotsStatus();
  const { data: pnlData } = usePnLData();
  
  const [selectedDesign, setSelectedDesign] = useState('compact');
  
  if (!botsData || botsData.length === 0) {
    return (
      <div className="p-8 text-center">
        <div className="animate-pulse">
          <div className="h-4 bg-gray-200 rounded w-1/4 mx-auto mb-4"></div>
          <div className="h-32 bg-gray-200 rounded"></div>
        </div>
      </div>
    );
  }

  // Get a sample of different temperature bots for demonstration
  const sampleBots = [
    botsData.find(bot => bot.temperature === 'HOT') || botsData[0],
    botsData.find(bot => bot.temperature === 'WARM') || botsData[1],
    botsData.find(bot => bot.temperature === 'COOL') || botsData[2],
    botsData.find(bot => bot.temperature === 'FROZEN') || botsData[3]
  ].filter(Boolean).slice(0, 4);

  const designs = [
    {
      id: 'compact',
      name: 'Compact Performance',
      description: 'Focus on P&L and key metrics with temperature gradient',
      component: CompactPerformanceCard
    },
    {
      id: 'advanced',
      name: 'Advanced Analytics',
      description: 'Rich data including market intelligence and trend analysis',
      component: AdvancedAnalyticsCard
    },
    {
      id: 'minimal',
      name: 'Minimal Modern',
      description: 'Clean design with elegant signal visualization',
      component: MinimalModernCard
    },
    {
      id: 'dense',
      name: 'Metric Dense',
      description: 'Maximum information density with organized grid layout',
      component: MetricDenseCard
    }
  ];

  const SelectedComponent = designs.find(d => d.id === selectedDesign)?.component || CompactPerformanceCard;

  return (
    <div className="p-8 max-w-7xl mx-auto">
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-gray-900 mb-2">Bot Card Design Samples</h1>
        <p className="text-gray-600 mb-6">
          Explore different approaches to displaying bot information. Each design emphasizes different aspects of trading data.
        </p>
        
        {/* Design Selector */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 mb-8">
          {designs.map((design) => (
            <button
              key={design.id}
              onClick={() => setSelectedDesign(design.id)}
              className={`p-4 rounded-lg border text-left transition-all ${
                selectedDesign === design.id
                  ? 'border-blue-500 bg-blue-50'
                  : 'border-gray-200 hover:border-gray-300 bg-white'
              }`}
            >
              <h3 className="font-semibold text-gray-900 mb-1">{design.name}</h3>
              <p className="text-sm text-gray-600">{design.description}</p>
            </button>
          ))}
        </div>
      </div>

      {/* Design Showcase */}
      <div className="mb-8">
        <h2 className="text-xl font-semibold text-gray-900 mb-4">
          {designs.find(d => d.id === selectedDesign)?.name} Design
        </h2>
        
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6">
          {sampleBots.map((bot) => (
            <SelectedComponent
              key={bot.id}
              bot={bot}
              pnlData={pnlData}
            />
          ))}
        </div>
      </div>

      {/* Design Analysis */}
      <div className="bg-gray-50 rounded-lg p-6">
        <h3 className="text-lg font-semibold text-gray-900 mb-4">Design Information</h3>
        
        {selectedDesign === 'compact' && (
          <div className="space-y-3">
            <h4 className="font-medium text-gray-900">Compact Performance Focus</h4>
            <ul className="text-sm text-gray-600 space-y-1">
              <li>• <strong>Temperature gradient</strong> - Visual temperature indication at top</li>
              <li>• <strong>P&L prominence</strong> - Large, color-coded profit/loss display</li>
              <li>• <strong>Signal strength bar</strong> - Visual representation of trading signals</li>
              <li>• <strong>Quick stats grid</strong> - Essential metrics in compact format</li>
              <li>• <strong>Win rate display</strong> - Success ratio for quick assessment</li>
            </ul>
          </div>
        )}
        
        {selectedDesign === 'advanced' && (
          <div className="space-y-3">
            <h4 className="font-medium text-gray-900">Advanced Analytics Integration</h4>
            <ul className="text-sm text-gray-600 space-y-1">
              <li>• <strong>Market regime analysis</strong> - TRENDING/CHOPPY detection with confidence</li>
              <li>• <strong>Signal direction icons</strong> - Clear BUY/SELL/HOLD indicators</li>
              <li>• <strong>Confidence meters</strong> - Visual confidence level representation</li>
              <li>• <strong>Position & risk display</strong> - Current position vs. max position</li>
              <li>• <strong>Trend intelligence</strong> - Market strength and volatility data</li>
            </ul>
          </div>
        )}
        
        {selectedDesign === 'minimal' && (
          <div className="space-y-3">
            <h4 className="font-medium text-gray-900">Minimal Modern Aesthetic</h4>
            <ul className="text-sm text-gray-600 space-y-1">
              <li>• <strong>Clean typography</strong> - Large, readable fonts with proper hierarchy</li>
              <li>• <strong>Bidirectional signal bar</strong> - Innovative BUY/SELL visualization</li>
              <li>• <strong>Subtle interactions</strong> - Gentle hover effects and transitions</li>
              <li>• <strong>Status indicators</strong> - Pulsing activity dots for running bots</li>
              <li>• <strong>Generous spacing</strong> - Comfortable padding for easy scanning</li>
            </ul>
          </div>
        )}
        
        {selectedDesign === 'dense' && (
          <div className="space-y-3">
            <h4 className="font-medium text-gray-900">Maximum Information Density</h4>
            <ul className="text-sm text-gray-600 space-y-1">
              <li>• <strong>6-metric grid</strong> - P&L, Win Rate, Trades, Signal, Position, Confidence</li>
              <li>• <strong>Icon categorization</strong> - Visual icons for each metric type</li>
              <li>• <strong>Color coding</strong> - Consistent color scheme for metric types</li>
              <li>• <strong>Trend analysis panel</strong> - Market regime and volatility data</li>
              <li>• <strong>Compact layout</strong> - Maximum data in minimal space</li>
            </ul>
          </div>
        )}
        
        <div className="mt-4 p-4 bg-blue-50 rounded-lg">
          <h4 className="font-medium text-blue-900 mb-2">Available Data Points</h4>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-sm text-blue-800">
            <div>
              <strong>Performance:</strong>
              <ul className="mt-1 space-y-1">
                <li>• Net P&L (USD)</li>
                <li>• ROI Percentage</li>
                <li>• Trade Count</li>
                <li>• Win/Loss Ratio</li>
                <li>• Total Spent/Received</li>
              </ul>
            </div>
            <div>
              <strong>Trading Intelligence:</strong>
              <ul className="mt-1 space-y-1">
                <li>• Signal Score (-1 to +1)</li>
                <li>• Temperature (HOT/WARM/COOL/FROZEN)</li>
                <li>• Trading Confidence</li>
                <li>• Market Regime Analysis</li>
                <li>• Position Sizing Data</li>
              </ul>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default BotCardDesignDemo;