import React from 'react';
import { useNewPairStats, useRecentNewPairs } from '../../hooks/useNewPairs';

interface TradingPair {
  product_id: string;
  base_name: string;
  initial_price?: number;
  initial_volume_24h?: number;
  first_seen: string;
}

const NewPairsCard: React.FC = () => {
  const { data: stats, isLoading: statsLoading } = useNewPairStats();
  const { data: recentPairs, isLoading: pairsLoading } = useRecentNewPairs(5);

  if (statsLoading || pairsLoading) {
    return (
      <div className="bg-white rounded-lg shadow-sm border p-6">
        <div className="flex items-center gap-2 mb-4">
          <span className="text-yellow-500">⚡</span>
          <h3 className="text-lg font-semibold">New Pair Detection</h3>
        </div>
        <div className="text-gray-500">Loading...</div>
      </div>
    );
  }

  return (
    <div className="bg-white rounded-lg shadow-sm border p-6">
      <div className="flex items-center gap-2 mb-4">
        <span className="text-yellow-500">⚡</span>
        <h3 className="text-lg font-semibold">New Pair Detection</h3>
        {stats?.stats.unprocessed_new_pairs > 0 && (
          <span className="bg-red-500 text-white px-2 py-1 rounded text-xs ml-2">
            {stats.stats.unprocessed_new_pairs} new
          </span>
        )}
      </div>
      
      <div className="space-y-4">
        {/* Stats Grid */}
        <div className="grid grid-cols-2 gap-4">
          <div className="space-y-1">
            <div className="flex items-center gap-2 text-sm text-gray-600">
              <span>🪙</span>
              Total Tracked
            </div>
            <div className="text-xl font-semibold">
              {stats?.stats.total_pairs_tracked.toLocaleString()}
            </div>
          </div>
          <div className="space-y-1">
            <div className="flex items-center gap-2 text-sm text-gray-600">
              <span>📈</span>
              USD Pairs
            </div>
            <div className="text-xl font-semibold">
              {stats?.stats.usd_pairs_tracked.toLocaleString()}
            </div>
          </div>
        </div>

        {/* Latest Discovery */}
        {stats?.stats.latest_discovery && (
          <div className="border rounded-lg p-3 bg-gray-50">
            <div className="flex items-center justify-between">
              <div>
                <div className="font-medium">
                  {stats.stats.latest_discovery.product_id}
                </div>
                <div className="text-sm text-gray-600">
                  {stats.stats.latest_discovery.base_name}
                </div>
              </div>
              <div className="text-right">
                <div className="flex items-center gap-1 text-sm text-gray-600">
                  <span>🕐</span>
                  Latest
                </div>
                <div className="text-xs text-gray-500">
                  {new Date(stats.stats.latest_discovery.discovered_at).toLocaleDateString()}
                </div>
              </div>
            </div>
          </div>
        )}

        {/* Recent Pairs */}
        {recentPairs && recentPairs.length > 0 && (
          <div className="space-y-2">
            <div className="text-sm font-medium">Recent Discoveries</div>
            <div className="space-y-1 max-h-32 overflow-y-auto">
              {recentPairs.slice(0, 3).map((pair: TradingPair) => (
                <div key={pair.product_id} className="flex items-center justify-between text-sm">
                  <div className="flex items-center gap-2">
                    <span className="bg-gray-100 px-2 py-1 rounded text-xs font-mono">
                      {pair.product_id}
                    </span>
                    <span className="text-gray-600 truncate max-w-24">
                      {pair.base_name}
                    </span>
                  </div>
                  <div className="text-gray-500 text-xs">
                    ${pair.initial_price?.toFixed(4) || 'N/A'}
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* System Info */}
        <div className="pt-2 border-t">
          <div className="flex items-center justify-between text-xs text-gray-500">
            <span>Scan Frequency</span>
            <span>{stats?.system_info.scan_frequency || 'Every 2 hours'}</span>
          </div>
          <div className="flex items-center justify-between text-xs text-gray-500">
            <span>Alert Threshold</span>
            <span>{stats?.system_info.alert_threshold || 'USD pairs only'}</span>
          </div>
        </div>
      </div>
    </div>
  );
};

export default NewPairsCard;
