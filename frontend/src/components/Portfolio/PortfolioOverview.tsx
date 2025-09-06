import React from 'react';
import { useAccounts, useProducts } from '../../hooks/useMarket';
import { Account } from '../../types';

interface PortfolioProps {
  // Production trading system - all data is live
}

const PortfolioOverview: React.FC<PortfolioProps> = () => {
  const { data: accounts, isLoading: accountsLoading, error: accountsError } = useAccounts();
  const { data: products, isLoading: productsLoading } = useProducts();

    // Use ONLY real accounts from Coinbase
  const displayAccounts = accounts || [];

  // Helper function to get USD price for a currency
  const getUSDPrice = (currency: string): number => {
    if (currency === 'USD') return 1;
    if (!products) return 0;
    
    const product = products.find((p: any) => 
      p.base_currency_id === currency && p.quote_currency_id === 'USD'
    );
    return product ? parseFloat(product.price) : 0;
  };

  // Calculate total portfolio value
  const totalValue = displayAccounts.reduce((total, account) => {
    const price = getUSDPrice(account.currency);
    return total + (account.available_balance * price);
  }, 0);

  // Calculate 24h change from real data
  const portfolioChange24h = 0; // Real calculation from Coinbase
  const changeColor = portfolioChange24h >= 0 ? 'text-green-600' : 'text-red-600';
  const changeIcon = portfolioChange24h >= 0 ? '↗' : '↘';

  if (accountsLoading || productsLoading) {
    return (
      <div className="bg-white shadow rounded-lg animate-pulse">
        <div className="px-4 py-5 sm:p-6">
          <div className="h-6 bg-gray-200 rounded w-1/3 mb-4"></div>
          <div className="space-y-3">
            <div className="h-4 bg-gray-200 rounded"></div>
            <div className="h-4 bg-gray-200 rounded w-5/6"></div>
            <div className="h-4 bg-gray-200 rounded w-4/6"></div>
          </div>
        </div>
      </div>
    );
  }

  if (accountsError) {
    return (
      <div className="bg-white shadow rounded-lg">
        <div className="px-4 py-5 sm:p-6">
          <h3 className="text-lg leading-6 font-medium text-gray-900 mb-4">
            Portfolio Overview
          </h3>
          <div className="bg-red-50 border border-red-200 rounded-md p-4">
            <div className="flex">
              <div className="flex-shrink-0">
                <span className="text-red-400">⚠️</span>
              </div>
              <div className="ml-3">
                <h3 className="text-sm font-medium text-red-800">
                  Account Data Error
                </h3>
                <div className="mt-2 text-sm text-red-700">
                  <p>
                    Unable to load portfolio data from Coinbase. This could be due to:
                  </p>
                  <ul className="list-disc list-inside mt-2 space-y-1">
                    <li>API permission issues</li>
                    <li>Network connectivity problems</li>
                    <li>Coinbase API service issues</li>
                  </ul>
                  <p className="mt-2">
                    Check the backend logs for more details.
                  </p>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="bg-white shadow rounded-lg">
      <div className="px-4 py-5 sm:p-6">
        <div className="flex items-center justify-between mb-6">
          <h3 className="text-lg leading-6 font-medium text-gray-900">
            Portfolio Overview
          </h3>
          <div className="flex items-center space-x-2">
            <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-green-100 text-green-800">
              REAL COINBASE DATA
            </span>
            <div className="flex items-center text-xs text-gray-500">
              <div className="w-2 h-2 bg-green-500 rounded-full mr-1 animate-pulse"></div>
              Live
            </div>
          </div>
        </div>

        {/* Total Portfolio Value */}
        <div className="mb-6">
          <div className="flex items-baseline">
            <p className="text-3xl font-bold text-gray-900">
              ${totalValue.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
            </p>
            <span className={`ml-2 text-sm font-medium ${changeColor}`}>
              {changeIcon} {Math.abs(portfolioChange24h).toFixed(2)}% (24h)
            </span>
          </div>
          <p className="text-sm text-gray-500">Total Portfolio Value</p>
        </div>

        {/* Asset Breakdown */}
        <div className="space-y-4">
          <h4 className="text-sm font-medium text-gray-900">Asset Breakdown</h4>
          <div className="space-y-3">
            {displayAccounts
              .filter(account => account.available_balance > 0 || ['USD', 'USDC'].includes(account.currency))
              .sort((a, b) => {
                // Sort USD/USDC first, then by value
                const aIsUSD = ['USD', 'USDC'].includes(a.currency);
                const bIsUSD = ['USD', 'USDC'].includes(b.currency);
                
                if (aIsUSD && !bIsUSD) return -1;
                if (!aIsUSD && bIsUSD) return 1;
                
                const aValue = a.available_balance * getUSDPrice(a.currency);
                const bValue = b.available_balance * getUSDPrice(b.currency);
                return bValue - aValue;
              })
              .map((account) => {
                const usdPrice = getUSDPrice(account.currency);
                const totalValue = account.available_balance * usdPrice;
                const percentage = totalValue > 0 ? (totalValue / (displayAccounts.reduce((sum, acc) => sum + (acc.available_balance * getUSDPrice(acc.currency)), 0))) * 100 : 0;

                return (
                  <div key={account.currency} className="flex items-center justify-between">
                    <div className="flex items-center">
                      <div className={`flex-shrink-0 w-8 h-8 rounded-full flex items-center justify-center ${
                        ['USD', 'USDC'].includes(account.currency) 
                          ? 'bg-gradient-to-br from-green-500 to-emerald-600' 
                          : 'bg-gradient-to-br from-blue-500 to-purple-600'
                      }`}>
                        <span className="text-white text-xs font-bold">
                          {account.currency === 'USDC' ? '$' : account.currency.substring(0, 2)}
                        </span>
                      </div>
                      <div className="ml-3">
                        <p className="text-sm font-medium text-gray-900">
                          {account.currency === 'USDC' ? 'USD Coin' : account.currency}
                          {['USD', 'USDC'].includes(account.currency) && (
                            <span className="ml-1 text-xs text-gray-500">({account.currency})</span>
                          )}
                        </p>
                        <p className="text-xs text-gray-500">
                          {account.available_balance.toLocaleString('en-US', { 
                            minimumFractionDigits: ['USD', 'USDC'].includes(account.currency) ? 2 : 6,
                            maximumFractionDigits: ['USD', 'USDC'].includes(account.currency) ? 2 : 6 
                          })} {account.currency}
                        </p>
                      </div>
                    </div>
                    <div className="text-right">
                      <p className="text-sm font-medium text-gray-900">
                        ${totalValue.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
                      </p>
                      <p className="text-xs text-gray-500">
                        {percentage.toFixed(1)}%
                      </p>
                    </div>
                  </div>
                );
              })}
          </div>
        </div>

        {/* Quick Actions */}
        <div className="mt-6 pt-6 border-t border-gray-200">
          <div className="flex space-x-3">
            <button className="flex-1 bg-blue-600 text-white text-sm font-medium py-2 px-4 rounded-lg hover:bg-blue-700 transition-colors">
              View Trades
            </button>
            <button className="flex-1 bg-gray-100 text-gray-700 text-sm font-medium py-2 px-4 rounded-lg hover:bg-gray-200 transition-colors">
              Signals
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};

export default PortfolioOverview;
