// Enhanced Bot Card with Product P&L Integration
import { useState, useEffect } from 'react';

interface ProductPerformance {
  product_id: string;
  trade_count: number;
  net_pnl: number;
  roi_percentage: number;
  active_days: number;
  trades_per_day: number;
}

const useProductPerformance = () => {
  const [performance, setPerformance] = useState<ProductPerformance[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchPerformance = async () => {
      try {
        const response = await fetch('/api/v1/raw-trades/pnl-by-product');
        const data = await response.json();
        setPerformance(data.products);
      } catch (error) {
        console.error('Error fetching clean product performance:', error);
      } finally {
        setLoading(false);
      }
    };

    fetchPerformance();
    // Refresh every 30 seconds
    const interval = setInterval(fetchPerformance, 30000);
    return () => clearInterval(interval);
  }, []);

  return { performance, loading };
};

export const ConsolidatedBotCardWithPerformance = ({ bot }: { bot: any }) => {
  const { performance, loading: _loading } = useProductPerformance();
  
  // Find performance data for this bot's product
  const botPerformance = performance.find(p => p.product_id === bot.pair);
  
  return (
    <div className="bg-white rounded-lg border shadow-sm p-4">
      {/* Existing bot status info */}
      <div className="flex items-center justify-between mb-3">
        <div className="flex items-center space-x-2">
          <span className="text-2xl">{bot.temperature === 'HOT' ? '🔥' : '❄️'}</span>
          <h3 className="font-medium text-gray-900">{bot.name}</h3>
        </div>
        <div className="text-sm text-gray-500">{bot.status}</div>
      </div>

      {/* NEW: Bot Performance Section */}
      {botPerformance && (
        <div className="mb-3 p-3 bg-gray-50 rounded border">
          <div className="flex items-center justify-between mb-2">
            <span className="text-sm font-medium text-gray-600">Performance</span>
            <span className="text-xs text-gray-400">{botPerformance.active_days}d</span>
          </div>
          
          <div className="grid grid-cols-2 gap-3 text-sm">
            <div>
              <div className="text-xs text-gray-500">Net P&L</div>
              <div className={`font-medium ${
                botPerformance.net_pnl >= 0 ? 'text-green-600' : 'text-red-600'
              }`}>
                ${botPerformance.net_pnl.toFixed(2)}
              </div>
            </div>
            
            <div>
              <div className="text-xs text-gray-500">ROI</div>
              <div className={`font-medium ${
                botPerformance.roi_percentage >= 0 ? 'text-green-600' : 'text-red-600'
              }`}>
                {botPerformance.roi_percentage.toFixed(1)}%
              </div>
            </div>
            
            <div>
              <div className="text-xs text-gray-500">Trades</div>
              <div className="font-medium text-gray-900">
                {botPerformance.trade_count}
              </div>
            </div>
            
            <div>
              <div className="text-xs text-gray-500">Per Day</div>
              <div className="font-medium text-gray-900">
                {botPerformance.trades_per_day.toFixed(1)}
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Existing trading intent, confirmation, etc. */}
      <div className="space-y-2">
        {/* Current bot status displays continue here */}
      </div>
    </div>
  );
};
