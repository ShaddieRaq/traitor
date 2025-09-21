import React, { useState } from 'react';
import { useMarketAnalysis } from '../hooks/useMarketAnalysis';
import { useNotifications } from '../hooks/useNotifications';
import NewPairsCard from './NewPairs/NewPairsCard';

const MarketAnalysis: React.FC = () => {
  const [limit, setLimit] = useState(50);
  const [includeGems, setIncludeGems] = useState(true);
  const [showNotifications, setShowNotifications] = useState(false);
  const { data: analysis, isLoading, error, refetch } = useMarketAnalysis(limit, includeGems);
  const { data: notificationsData } = useNotifications(50, false);

  const getRiskColor = (color: string) => {
    switch (color) {
      case 'green': return 'text-green-600 bg-green-100';
      case 'yellow': return 'text-yellow-600 bg-yellow-100';
      case 'red': return 'text-red-600 bg-red-100';
      default: return 'text-gray-600 bg-gray-100';
    }
  };

  const getRecommendationColor = (color: string) => {
    switch (color) {
      case 'green': return 'text-green-700 bg-green-50 border-green-200';
      case 'yellow': return 'text-yellow-700 bg-yellow-50 border-yellow-200';
      default: return 'text-gray-700 bg-gray-50 border-gray-200';
    }
  };

  const formatRecommendation = (rec: string) => {
    switch (rec) {
      case 'HIGHLY_RECOMMENDED': return 'Highly Recommended';
      case 'GOOD_CANDIDATE': return 'Good Candidate';
      case 'CONSIDER_LATER': return 'Consider Later';
      default: return rec;
    }
  };

  const triggerFreshAnalysis = async () => {
    try {
      const response = await fetch('/api/v1/market-analysis/trigger-scan', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
      });
      
      if (response.ok) {
        const result = await response.json();
        // Refetch the live analysis data
        refetch();
        alert(`✅ Fresh market analysis triggered!\n\nTask ID: ${result.task_id}\n\nData will refresh automatically in a few minutes.`);
      } else {
        throw new Error('Failed to trigger analysis');
      }
    } catch (error) {
      console.error('Error triggering market analysis:', error);
      alert('❌ Failed to trigger market analysis. Please try again.');
    }
  };

  if (isLoading) {
    return (
      <div className="bg-white rounded-lg shadow p-6">
        <div className="animate-pulse">
          <div className="h-8 bg-gray-200 rounded w-1/3 mb-4"></div>
          <div className="space-y-4">
            {[...Array(5)].map((_, i) => (
              <div key={i} className="h-24 bg-gray-100 rounded"></div>
            ))}
          </div>
        </div>
      </div>
    );
  }

  if (error || !analysis) {
    return (
      <div className="bg-white rounded-lg shadow p-6">
        <h2 className="text-xl font-semibold text-gray-900 mb-4">Market Analysis</h2>
        <div className="bg-red-50 border border-red-200 rounded-md p-4">
          <p className="text-red-700">
            {error ? 'Failed to load market analysis' : 'No analysis data available'}
          </p>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* New Pairs Detection Card */}
      <NewPairsCard />
      
      {/* Header */}
      <div className="bg-white rounded-lg shadow p-6">
        <div className="flex justify-between items-center mb-4">
          <div>
            <h2 className="text-2xl font-bold text-gray-900">Market Analysis</h2>
            <p className="text-sm text-gray-600 mt-1">
              🤖 Auto-scans every hour • 💎 Gem hunting enabled • {notificationsData?.unread_count || 0} unread opportunities
            </p>
          </div>
          <div className="flex items-center space-x-4">
            {/* Trigger Fresh Analysis */}
            <button
              onClick={triggerFreshAnalysis}
              className="bg-green-600 text-white px-4 py-2 rounded-md hover:bg-green-700 transition-colors text-sm font-medium"
            >
              🚀 Trigger Fresh Scan
            </button>
            
            <label className="flex items-center">
              <span className="text-sm font-medium text-gray-700 mr-2">Analyze top:</span>
              <select
                value={limit}
                onChange={(e) => setLimit(Number(e.target.value))}
                className="border border-gray-300 rounded-md px-3 py-1 text-sm"
              >
                <option value={25}>25 pairs</option>
                <option value={50}>50 pairs</option>
                <option value={100}>100 pairs</option>
                <option value={200}>200 pairs</option>
              </select>
            </label>
            
            <label className="flex items-center">
              <input
                type="checkbox"
                checked={includeGems}
                onChange={(e) => setIncludeGems(e.target.checked)}
                className="mr-2"
              />
              <span className="text-sm font-medium text-gray-700">💎 Include Gems</span>
            </label>
          </div>
        </div>

        {/* Summary Stats */}
        <div className="grid grid-cols-1 md:grid-cols-5 gap-4 mb-6">
          <div className="bg-blue-50 p-4 rounded-lg">
            <div className="text-2xl font-bold text-blue-600">{analysis.active_bots_count}</div>
            <div className="text-sm text-blue-700">Active Bots</div>
          </div>
          <div className="bg-green-50 p-4 rounded-lg">
            <div className="text-2xl font-bold text-green-600">{analysis.summary.counts.highly_recommended}</div>
            <div className="text-sm text-green-700">Highly Recommended</div>
          </div>
          <div className="bg-yellow-50 p-4 rounded-lg">
            <div className="text-2xl font-bold text-yellow-600">{analysis.summary.counts.good_candidates}</div>
            <div className="text-sm text-yellow-700">Good Candidates</div>
          </div>
          <div className="bg-purple-50 p-4 rounded-lg">
            <div className="text-2xl font-bold text-purple-600">{analysis.total_analyzed}</div>
            <div className="text-sm text-purple-700">Total Analyzed</div>
          </div>
          <div className="bg-orange-50 p-4 rounded-lg">
            <div className="text-2xl font-bold text-orange-600">{notificationsData?.unread_count || 0}</div>
            <div className="text-sm text-orange-700">Auto-Discovered</div>
          </div>
        </div>

        {/* Top Recommendation */}
        {analysis.summary.top_recommendation && (
          <div className="bg-gradient-to-r from-green-50 to-blue-50 border border-green-200 rounded-lg p-6 mb-6">
            <h3 className="text-lg font-semibold text-gray-900 mb-3">🏆 Top Recommendation</h3>
            <div className="flex justify-between items-start">
              <div>
                <div className="text-xl font-bold text-gray-900">
                  {analysis.summary.top_recommendation.product_id}
                </div>
                <div className="text-sm text-gray-600 mb-2">
                  {analysis.summary.top_recommendation.base_name}
                </div>
                <div className="flex items-center space-x-4 text-sm">
                  <span className="text-gray-700">
                    ${analysis.summary.top_recommendation.price.toFixed(2)}
                  </span>
                  <span className="text-gray-700">
                    ${analysis.summary.top_recommendation.volume_24h_million.toFixed(1)}M volume
                  </span>
                  <span className={`px-2 py-1 rounded text-xs font-medium ${getRiskColor(analysis.summary.top_recommendation.risk_color)}`}>
                    {analysis.summary.top_recommendation.risk_level} Risk
                  </span>
                </div>
              </div>
              <div className="text-right">
                <div className="text-2xl font-bold text-green-600">
                  {analysis.summary.top_recommendation.total_score.toFixed(1)}
                </div>
                <div className="text-sm text-gray-600">Total Score</div>
              </div>
            </div>
          </div>
        )}

        {/* Category Leaders */}
        <div className="bg-white rounded-lg shadow p-6 mb-6">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">Category Leaders</h3>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div className="bg-blue-50 p-4 rounded-lg">
              <h4 className="font-medium text-blue-900 mb-2">🏆 Best Liquidity</h4>
              <div className="text-lg font-semibold text-blue-700">
                {analysis.summary.best_by_category.liquidity.product_id}
              </div>
              <div className="text-sm text-blue-600">
                ${analysis.summary.best_by_category.liquidity.volume.toFixed(1)}M volume
              </div>
            </div>
            <div className="bg-green-50 p-4 rounded-lg">
              <h4 className="font-medium text-green-900 mb-2">📈 Most Volatile</h4>
              <div className="text-lg font-semibold text-green-700">
                {analysis.summary.best_by_category.volatility.product_id}
              </div>
              <div className="text-sm text-green-600">
                {analysis.summary.best_by_category.volatility.change > 0 ? '+' : ''}
                {analysis.summary.best_by_category.volatility.change.toFixed(2)}% change
              </div>
            </div>
            <div className="bg-purple-50 p-4 rounded-lg">
              <h4 className="font-medium text-purple-900 mb-2">🚀 Best Momentum</h4>
              <div className="text-lg font-semibold text-purple-700">
                {analysis.summary.best_by_category.momentum.product_id}
              </div>
              <div className="text-sm text-purple-600">
                +{analysis.summary.best_by_category.momentum.growth.toFixed(1)}% volume growth
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Detailed Analysis Table */}
      <div className="bg-white rounded-lg shadow overflow-hidden">
        <div className="px-6 py-4 border-b border-gray-200">
          <div className="flex justify-between items-center">
            <div>
              <h3 className="text-lg font-semibold text-gray-900">Detailed Analysis</h3>
              <p className="text-sm text-gray-600 mt-1">
                Excluding current bot pairs: {analysis.excluded_pairs.join(', ')}
              </p>
            </div>
            <div className="text-sm text-gray-500">
              {analysis.candidates.length} results • Scroll to see all
            </div>
          </div>
        </div>
        
        {/* Fixed height scrollable container */}
        <div className="overflow-auto max-h-96">
          <table className="min-w-full divide-y divide-gray-200">
            <thead className="bg-gray-50 sticky top-0 z-10">
              <tr>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider bg-gray-50">
                  Trading Pair
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider bg-gray-50">
                  Price & Volume
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider bg-gray-50">
                  24h Changes
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider bg-gray-50">
                  Scores
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider bg-gray-50">
                  Risk & Recommendation
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider bg-gray-50">
                  Total Score
                </th>
              </tr>
            </thead>
            <tbody className="bg-white divide-y divide-gray-200">
              {analysis.candidates.map((candidate, index) => (
                <tr key={candidate.product_id} className={index < 3 ? 'bg-yellow-50' : ''}>
                  <td className="px-6 py-4 whitespace-nowrap">
                    <div className="flex items-center">
                      <div>
                        <div className="text-sm font-medium text-gray-900">
                          {candidate.product_id}
                        </div>
                        <div className="text-sm text-gray-500">
                          {candidate.base_name}
                        </div>
                      </div>
                    </div>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                    <div>${candidate.price.toFixed(2)}</div>
                    <div className="text-gray-500">
                      ${candidate.volume_24h_million.toFixed(1)}M vol
                    </div>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm">
                    <div className={candidate.price_change_24h >= 0 ? 'text-green-600' : 'text-red-600'}>
                      {candidate.price_change_24h > 0 ? '+' : ''}{candidate.price_change_24h.toFixed(2)}%
                    </div>
                    <div className={candidate.volume_change_24h >= 0 ? 'text-green-500' : 'text-red-500'}>
                      Vol: {candidate.volume_change_24h > 0 ? '+' : ''}{candidate.volume_change_24h.toFixed(1)}%
                    </div>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                    <div className="space-y-1">
                      <div>L: {candidate.liquidity_score.toFixed(1)}/10</div>
                      <div>V: {candidate.volatility_score.toFixed(1)}/10</div>
                      <div>M: {candidate.momentum_score.toFixed(1)}/5</div>
                    </div>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    <div className="flex flex-col space-y-2">
                      <span className={`inline-flex px-2 py-1 text-xs font-semibold rounded-full ${getRiskColor(candidate.risk_color)}`}>
                        {candidate.risk_level}
                      </span>
                      <span className={`inline-flex px-2 py-1 text-xs font-semibold rounded border ${getRecommendationColor(candidate.recommendation_color)}`}>
                        {formatRecommendation(candidate.recommendation)}
                      </span>
                    </div>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    <div className="text-lg font-semibold text-gray-900">
                      {candidate.total_score.toFixed(1)}
                    </div>
                    <div className="text-sm text-gray-500">/25</div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {/* Auto-Discovered Opportunities */}
      {notificationsData?.notifications && notificationsData.notifications.length > 0 && (
        <div className="bg-white rounded-lg shadow p-6">
          <div className="flex justify-between items-center mb-4">
            <h3 className="text-lg font-semibold text-gray-900">🤖 Recent Auto-Discoveries</h3>
            <span className="text-sm text-gray-500">
              {notificationsData.notifications.filter(n => n.type === 'market_opportunity').length} opportunities found
            </span>
          </div>
          <div className="space-y-3">
            {notificationsData.notifications
              .filter(n => n.type === 'market_opportunity')
              .slice(0, 3)
              .map((notification) => {
                // Extract trading pairs from notification message
                const pairs = notification.message.match(/\*\*([A-Z]+-USD)\*\*/g)?.map(match => 
                  match.replace(/\*\*/g, '')
                ) || [];
                
                return (
                  <div key={notification.id} className="bg-gradient-to-r from-blue-50 to-green-50 border border-blue-200 rounded-lg p-4">
                    <div className="flex justify-between items-start">
                      <div className="flex-1">
                        <div className="flex items-center space-x-2 mb-2">
                          <span className="text-lg">🎯</span>
                          <h4 className="font-medium text-gray-900">{notification.title}</h4>
                          {!notification.read && (
                            <span className="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-orange-100 text-orange-800">
                              New
                            </span>
                          )}
                        </div>
                        <div className="flex flex-wrap gap-2 mb-2">
                          {pairs.slice(0, 4).map((pair, pairIndex) => (
                            <span 
                              key={pairIndex}
                              className="inline-flex items-center px-2 py-1 rounded text-xs font-medium bg-blue-100 text-blue-800"
                            >
                              {pair}
                            </span>
                          ))}
                          {pairs.length > 4 && (
                            <span className="inline-flex items-center px-2 py-1 rounded text-xs font-medium bg-gray-100 text-gray-800">
                              +{pairs.length - 4} more
                            </span>
                          )}
                        </div>
                        <div className="text-xs text-gray-500">
                          Discovered: {notification.time_ago}
                        </div>
                      </div>
                      <div className="ml-4">
                        <span className={`inline-flex items-center px-2 py-1 rounded-full text-xs font-medium ${
                          notification.priority === 'high' 
                            ? 'bg-orange-100 text-orange-800' 
                            : 'bg-blue-100 text-blue-800'
                        }`}>
                          {notification.priority.toUpperCase()}
                        </span>
                      </div>
                    </div>
                  </div>
                );
              })}
          </div>
          {notificationsData.notifications.filter(n => n.type === 'market_opportunity').length > 3 && (
            <div className="mt-4 text-center">
              <button
                onClick={() => setShowNotifications(true)}
                className="text-blue-600 hover:text-blue-800 text-sm font-medium"
              >
                View all {notificationsData.notifications.filter(n => n.type === 'market_opportunity').length} discoveries →
              </button>
            </div>
          )}
        </div>
      )}
    </div>
  );
};

export default MarketAnalysis;
