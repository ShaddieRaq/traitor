import React from 'react';
import { EnhancedBotStatus } from '../../types';

interface BalanceStatusIndicatorProps {
  bots: EnhancedBotStatus[];
}

const BalanceStatusIndicator: React.FC<BalanceStatusIndicatorProps> = ({ bots }) => {
  // Calculate overall balance status from bot trade readiness
  const getBalanceStatus = () => {
    if (!bots || bots.length === 0) {
      return {
        status: 'unknown',
        message: 'No bots active',
        color: 'bg-gray-400',
        icon: '❓'
      };
    }

    const blockedByBalance = bots.filter(bot => 
      bot.trade_readiness?.blocking_reason?.includes('insufficient_balance')
    );

    const canTradeCount = bots.filter(bot => bot.trade_readiness?.can_trade).length;
    const totalActive = bots.filter(bot => bot.status === 'RUNNING').length;

    if (blockedByBalance.length === 0) {
      return {
        status: 'sufficient',
        message: `All ${totalActive} bots can trade`,
        color: 'bg-green-500',
        icon: '💰',
        details: `${canTradeCount}/${totalActive} ready to trade`
      };
    }

    if (blockedByBalance.length === totalActive) {
      return {
        status: 'insufficient',
        message: 'Insufficient funds for trading',
        color: 'bg-red-500',
        icon: '⚠️',
        details: `${blockedByBalance.length} bots blocked by low balance`
      };
    }

    return {
      status: 'low',
      message: 'Limited trading capacity',
      color: 'bg-yellow-500',
      icon: '⚡',
      details: `${blockedByBalance.length}/${totalActive} bots blocked`
    };
  };

  const balanceStatus = getBalanceStatus();

  // Extract balance information from blocking reasons
  const getBalanceDetails = () => {
    const blockedBot = bots.find(bot => 
      bot.trade_readiness?.blocking_reason?.includes('insufficient_balance')
    );
    
    if (blockedBot?.trade_readiness?.blocking_reason) {
      const reason = blockedBot.trade_readiness.blocking_reason;
      const match = reason.match(/\$([0-9.]+)\s+available,\s+\$([0-9.]+)\s+required/);
      if (match) {
        const available = parseFloat(match[1]);
        const required = parseFloat(match[2]);
        return {
          available,
          required,
          shortfall: required - available
        };
      }
    }
    return null;
  };

  const balanceDetails = getBalanceDetails();

  return (
    <div className="bg-white border rounded-lg p-4">
      <div className="flex items-center justify-between">
        <div className="flex items-center">
          <div className={`w-3 h-3 rounded-full mr-3 ${balanceStatus.color}`}></div>
          <div>
            <div className="text-sm font-medium text-gray-900">
              {balanceStatus.icon} {balanceStatus.message}
            </div>
            <div className="text-xs text-gray-500 mt-0.5">
              {balanceStatus.details}
            </div>
          </div>
        </div>
        
        {balanceDetails && (
          <div className="text-right">
            <div className="text-sm font-medium text-gray-900">
              ${balanceDetails.available.toFixed(2)}
            </div>
            <div className="text-xs text-gray-500">
              Available
            </div>
            {balanceStatus.status !== 'sufficient' && (
              <div className="text-xs text-red-600 mt-1">
                ${balanceDetails.shortfall.toFixed(2)} needed
              </div>
            )}
          </div>
        )}
      </div>
      
      {balanceStatus.status === 'insufficient' && (
        <div className="mt-3 p-3 bg-red-50 border border-red-200 rounded">
          <div className="text-sm text-red-800">
            <strong>Action Required:</strong> Add funds to enable trading
          </div>
          {balanceDetails && (
            <div className="text-xs text-red-600 mt-1">
              Minimum required: ${balanceDetails.required.toFixed(2)}
            </div>
          )}
        </div>
      )}
      
      {balanceStatus.status === 'low' && (
        <div className="mt-3 p-3 bg-yellow-50 border border-yellow-200 rounded">
          <div className="text-sm text-yellow-800">
            <strong>Warning:</strong> Limited funds may restrict trading opportunities
          </div>
        </div>
      )}
    </div>
  );
};

export default BalanceStatusIndicator;
