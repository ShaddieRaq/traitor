import React from 'react';
import { useProducts } from '../../hooks/useMarket';

interface MarketTickerProps {
  limit?: number;
}

const MarketTicker: React.FC<MarketTickerProps> = ({ limit = 6 }) => {
  const { data: products, isLoading, error } = useProducts();

  if (isLoading) {
    return (
      <div className="bg-white shadow rounded-lg animate-pulse">
        <div className="px-4 py-3">
          <div className="flex space-x-6">
            {[...Array(4)].map((_, i) => (
              <div key={i} className="flex items-center space-x-2">
                <div className="h-4 bg-gray-200 rounded w-12"></div>
                <div className="h-4 bg-gray-200 rounded w-16"></div>
              </div>
            ))}
          </div>
        </div>
      </div>
    );
  }

  if (error || !products) {
    return (
      <div className="bg-white shadow rounded-lg">
        <div className="px-4 py-3">
          <div className="text-red-600 text-sm">
            Unable to load market data
          </div>
        </div>
      </div>
    );
  }

  // Filter for major trading pairs and sort by volume
  const majorPairs = products
    .filter((product: any) => 
      product.quote_currency_id === 'USD' && 
      ['BTC', 'ETH', 'SOL', 'ADA', 'DOT', 'LINK', 'MATIC', 'AVAX'].includes(product.base_currency_id)
    )
    .sort((a: any, b: any) => parseFloat(b.volume_24h) - parseFloat(a.volume_24h))
    .slice(0, limit);

  return (
    <div className="bg-white shadow rounded-lg">
      <div className="px-4 py-3">
        <div className="flex items-center justify-between mb-2">
          <h4 className="text-sm font-medium text-gray-900">Market Overview</h4>
          <div className="flex items-center space-x-2">
            <div className="flex items-center text-xs text-gray-500">
              <div className="w-2 h-2 bg-green-500 rounded-full mr-1 animate-pulse"></div>
              Live
            </div>
            <span className="text-xs text-gray-500">Updates every 5s</span>
          </div>
        </div>
        
        <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-4">
          {majorPairs.map((product: any) => {
            const price = parseFloat(product.price);
            const change24h = parseFloat(product.price_percentage_change_24h);
            const isPositive = change24h >= 0;
            
            return (
              <div key={product.product_id} className="text-center">
                <div className="flex items-center justify-center space-x-1 mb-1">
                  <span className="text-sm font-bold text-gray-900">
                    {product.base_display_symbol}
                  </span>
                  <span className={`text-xs ${isPositive ? 'text-green-600' : 'text-red-600'}`}>
                    {isPositive ? '↗' : '↘'}
                  </span>
                </div>
                
                <div className="text-sm font-medium text-gray-900">
                  ${price.toLocaleString('en-US', { 
                    minimumFractionDigits: price > 1 ? 2 : 6,
                    maximumFractionDigits: price > 1 ? 2 : 6
                  })}
                </div>
                
                <div className={`text-xs font-medium ${isPositive ? 'text-green-600' : 'text-red-600'}`}>
                  {isPositive ? '+' : ''}{change24h.toFixed(2)}%
                </div>
              </div>
            );
          })}
        </div>
      </div>
    </div>
  );
};

export default MarketTicker;
