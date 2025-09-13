import React from 'react';
import { useQuery } from '@tanstack/react-query';

const PnLValidation: React.FC = () => {
  const { data: profitabilityData } = useQuery({
    queryKey: ['profitability-clean'],
    queryFn: async () => {
      const response = await fetch('/api/v1/raw-trades/stats');
      return response.json();
    },
    refetchInterval: 30000,
  });

  // Manual validation check
  const validationStatus = React.useMemo(() => {
    if (!profitabilityData) return { status: 'loading', message: 'Loading data...' };
    
    const checks = {
      hasTradeData: profitabilityData.total_trades > 0,
      reasonablePnL: profitabilityData.net_pnl > -200000 && profitabilityData.net_pnl < 200000,
      buySelIBalance: profitabilityData.buy_trades + profitabilityData.sell_trades === profitabilityData.total_trades,
      hasReasonableVolume: profitabilityData.total_volume_usd > 0
    };
    
    const allPassed = Object.values(checks).every(Boolean);
    
    return {
      status: allPassed ? 'valid' : 'warning',
      message: allPassed ? 'All validation checks passed' : 'Some validation checks failed',
      checks
    };
  }, [profitabilityData]);

  if (!profitabilityData) {
    return (
      <div className="bg-gray-100 rounded-lg p-4">
        <h3 className="font-semibold text-gray-700 mb-2">🔍 Data Validation</h3>
        <p className="text-gray-600">Loading validation data...</p>
      </div>
    );
  }

  return (
    <div className={`rounded-lg p-4 ${
      validationStatus.status === 'valid' ? 'bg-green-50 border border-green-200' : 
      validationStatus.status === 'warning' ? 'bg-yellow-50 border border-yellow-200' :
      'bg-gray-100'
    }`}>
      <h3 className="font-semibold mb-2 flex items-center gap-2">
        {validationStatus.status === 'valid' && <span className="text-green-600">✅</span>}
        {validationStatus.status === 'warning' && <span className="text-yellow-600">⚠️</span>}
        🔍 P&L Data Validation
      </h3>
      
      <div className="text-sm space-y-1">
        <p className={
          validationStatus.status === 'valid' ? 'text-green-700' :
          validationStatus.status === 'warning' ? 'text-yellow-700' :
          'text-gray-600'
        }>
          {validationStatus.message}
        </p>
        
        <div className="mt-3 grid grid-cols-2 gap-2 text-xs">
          <div>
            <span className="font-medium">Total Trades:</span> {profitabilityData.total_trades}
          </div>
          <div>
            <span className="font-medium">Buy/Sell:</span> {profitabilityData.buy_trades}/{profitabilityData.sell_trades}
          </div>
          <div>
            <span className="font-medium">Volume:</span> ${profitabilityData.total_volume_usd?.toFixed(0)}
          </div>
          <div>
            <span className="font-medium">P&L:</span> 
            <span className={profitabilityData.net_pnl >= 0 ? 'text-green-600' : 'text-red-600'}>
              ${profitabilityData.net_pnl?.toFixed(0)}
            </span>
          </div>
        </div>

        {validationStatus.checks && (
          <div className="mt-3 pt-2 border-t border-gray-200">
            <p className="text-xs text-gray-500 mb-1">Validation Checks:</p>
            <div className="grid grid-cols-2 gap-1 text-xs">
              {Object.entries(validationStatus.checks).map(([check, passed]) => (
                <div key={check} className="flex items-center gap-1">
                  <span>{passed ? '✅' : '❌'}</span>
                  <span className="text-gray-600">
                    {check.replace(/([A-Z])/g, ' $1').toLowerCase()}
                  </span>
                </div>
              ))}
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default PnLValidation;
