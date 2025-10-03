import React, { useState } from 'react';
import { useTrades, Trade } from '../hooks/useTrades';
import { TradeExecutionFeed } from '../components/Trading/TradeExecutionFeed';
import { useTradeExecutionUpdates } from '../hooks/useTradeExecutionUpdates';
import { TrendingUp, TrendingDown, Activity, RefreshCw } from 'lucide-react';

// Trade Statistics Component
const TradeStats: React.FC = () => {
  const [stats, setStats] = React.useState<any>(null);
  
  React.useEffect(() => {
    fetch('/api/v1/raw-trades/stats')
      .then(res => res.json())
      .then(setStats)
      .catch(console.error);
  }, []);

  if (!stats) return null;

  return (
    <div className="grid grid-cols-1 md:grid-cols-5 gap-4 mb-6">
      <div className="bg-white p-4 rounded-lg shadow border">
        <div className="flex items-center">
          <Activity className="h-5 w-5 text-blue-500 mr-2" />
          <div>
            <p className="text-sm font-medium text-gray-600">Total Trades</p>
            <p className="text-2xl font-bold text-gray-900">{stats.total_trades?.toLocaleString()}</p>
          </div>
        </div>
      </div>
      
      <div className="bg-white p-4 rounded-lg shadow border">
        <div className="flex items-center">
          <div className="mr-2">🏷️</div>
          <div>
            <p className="text-sm font-medium text-gray-600">Products</p>
            <p className="text-2xl font-bold text-gray-900">{stats.total_products}</p>
          </div>
        </div>
      </div>
      
      <div className="bg-white p-4 rounded-lg shadow border">
        <div className="flex items-center">
          <div className="mr-2">💰</div>
          <div>
            <p className="text-sm font-medium text-gray-600">Volume</p>
            <p className="text-2xl font-bold text-gray-900">${stats.total_volume_usd?.toLocaleString()}</p>
          </div>
        </div>
      </div>
      
      <div className="bg-white p-4 rounded-lg shadow border">
        <div className="flex items-center">
          <div className="mr-2">💸</div>
          <div>
            <p className="text-sm font-medium text-gray-600">Fees</p>
            <p className="text-2xl font-bold text-gray-900">${stats.total_fees?.toFixed(2)}</p>
          </div>
        </div>
      </div>
      
      <div className="bg-white p-4 rounded-lg shadow border">
        <div className="flex items-center">
          {stats.net_pnl >= 0 ? (
            <TrendingUp className="h-5 w-5 text-green-500 mr-2" />
          ) : (
            <TrendingDown className="h-5 w-5 text-red-500 mr-2" />
          )}
          <div>
            <p className="text-sm font-medium text-gray-600">Net P&L</p>
            <p className={`text-2xl font-bold ${stats.net_pnl >= 0 ? 'text-green-600' : 'text-red-600'}`}>
              ${stats.net_pnl?.toFixed(2)}
            </p>
          </div>
        </div>
      </div>
    </div>
  );
};

// Trade History Table Component
const TradeHistoryTable: React.FC<{ trades: Trade[], isLoading: boolean }> = ({ trades, isLoading }) => {
  if (isLoading) {
    return (
      <div className="bg-white shadow rounded-lg">
        <div className="px-4 py-5 sm:p-6 text-center">
          <RefreshCw className="h-8 w-8 animate-spin mx-auto text-gray-400 mb-2" />
          <p className="text-gray-500">Loading trade history...</p>
        </div>
      </div>
    );
  }

  if (!trades?.length) {
    return (
      <div className="bg-white shadow rounded-lg">
        <div className="px-4 py-5 sm:p-6 text-center">
          <Activity className="h-12 w-12 mx-auto text-gray-400 mb-4" />
          <h3 className="text-lg font-medium text-gray-900 mb-2">No trades found</h3>
          <p className="text-gray-500">Your trading history will appear here once trades are executed.</p>
        </div>
      </div>
    );
  }

  return (
    <div className="bg-white shadow rounded-lg overflow-hidden">
      <div className="px-4 py-5 border-b border-gray-200 sm:px-6">
        <h3 className="text-lg leading-6 font-medium text-gray-900">Trade History</h3>
        <p className="mt-1 text-sm text-gray-500">Recent trading activity and execution history</p>
      </div>
      
      <div className="overflow-x-auto">
        <table className="min-w-full divide-y divide-gray-200">
          <thead className="bg-gray-50">
            <tr>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Time
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Product
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Side
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Size
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Price
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Value
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Fees
              </th>
            </tr>
          </thead>
          <tbody className="bg-white divide-y divide-gray-200">
            {trades.map((trade) => (
              <tr key={trade.id} className="hover:bg-gray-50">
                <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                  {new Date(trade.created_at).toLocaleString()}
                </td>
                <td className="px-6 py-4 whitespace-nowrap">
                  <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-blue-100 text-blue-800">
                    {trade.product_id}
                  </span>
                </td>
                <td className="px-6 py-4 whitespace-nowrap">
                  <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${
                    trade.side === 'BUY' 
                      ? 'bg-green-100 text-green-800' 
                      : 'bg-red-100 text-red-800'
                  }`}>
                    {trade.side === 'BUY' ? '🟢 BUY' : '🔴 SELL'}
                  </span>
                </td>
                <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                  {trade.size.toFixed(6)}
                </td>
                <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                  ${trade.price.toFixed(4)}
                </td>
                <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">
                  ${trade.usd_value.toFixed(2)}
                </td>
                <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                  ${trade.commission.toFixed(4)}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
};

const Trades: React.FC = () => {
  const [tradeLimit, setTradeLimit] = useState(50);
  const [selectedFilter, setSelectedFilter] = useState('all');
  const { data: trades = [], isLoading, error, refetch } = useTrades(tradeLimit);
  const { updates: tradeUpdates } = useTradeExecutionUpdates();

  // Filter trades based on selection
  const filteredTrades = React.useMemo(() => {
    if (selectedFilter === 'all') return trades;
    return trades.filter(trade => trade.side.toLowerCase() === selectedFilter);
  }, [trades, selectedFilter]);

  const handleRefresh = () => {
    refetch();
  };

  if (error) {
    return (
      <div className="space-y-6">
        <div className="bg-red-50 border border-red-200 rounded-md p-4">
          <div className="text-red-800">
            Error loading trades. Please check your API connection.
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="md:flex md:items-center md:justify-between">
        <div className="flex-1 min-w-0">
          <h2 className="text-2xl font-bold leading-7 text-gray-900 sm:text-3xl sm:truncate">
            Trading Activity
          </h2>
          <p className="mt-1 text-sm text-gray-500">
            Complete trading history, recent activity, and performance metrics
          </p>
        </div>
        
        <div className="mt-4 flex space-x-3 md:mt-0 md:ml-4">
          {/* Filter Dropdown */}
          <select
            value={selectedFilter}
            onChange={(e) => setSelectedFilter(e.target.value)}
            className="inline-flex items-center px-3 py-2 border border-gray-300 rounded-md shadow-sm text-sm font-medium text-gray-700 bg-white hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
          >
            <option value="all">All Trades</option>
            <option value="buy">Buy Orders</option>
            <option value="sell">Sell Orders</option>
          </select>
          
          {/* Refresh Button */}
          <button
            onClick={handleRefresh}
            className="inline-flex items-center px-3 py-2 border border-gray-300 rounded-md shadow-sm text-sm font-medium text-gray-700 bg-white hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
          >
            <RefreshCw className="h-4 w-4 mr-2" />
            Refresh
          </button>
        </div>
      </div>

      {/* Trade Statistics */}
      <TradeStats />

      {/* Recent Activity Feed - Only show if there are active updates */}
      {tradeUpdates.length > 0 && (
        <div className="bg-white rounded-lg shadow border">
          <div className="px-4 py-3 border-b border-gray-200">
            <h3 className="text-lg font-medium text-gray-900">Live Trade Execution</h3>
            <p className="text-sm text-gray-600">Real-time trading activity and order status</p>
          </div>
          <div className="p-4">
            <TradeExecutionFeed />
          </div>
        </div>
      )}

      {/* Trade History Table */}
      <TradeHistoryTable trades={filteredTrades} isLoading={isLoading} />
      
      {/* Load More Button */}
      {trades.length >= tradeLimit && (
        <div className="text-center">
          <button
            onClick={() => setTradeLimit(prev => prev + 50)}
            className="inline-flex items-center px-4 py-2 border border-gray-300 rounded-md shadow-sm text-sm font-medium text-gray-700 bg-white hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
          >
            Load More Trades
          </button>
        </div>
      )}
    </div>
  );
};

export default Trades;
