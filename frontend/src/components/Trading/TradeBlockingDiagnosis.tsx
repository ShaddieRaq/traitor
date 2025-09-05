import React from 'react';
import { EnhancedBotStatus } from '../../types';

interface TradeBlockingDiagnosisProps {
  bot: EnhancedBotStatus;
  className?: string;
}

const TradeBlockingDiagnosis: React.FC<TradeBlockingDiagnosisProps> = ({ bot, className = '' }) => {
  const botData = bot as any;
  
  // Get simple, clear status
  const status = botData.trade_readiness?.status;
  const nextAction = botData.trading_intent?.next_action || 'hold';
  const signalStrength = Math.round((botData.trading_intent?.signal_strength || 0) * 100);
  const canTrade = botData.trade_readiness?.can_trade;

  // Simple status explanations
  const getStatusInfo = () => {
    switch (status) {
      case 'no_signal':
        return {
          title: 'Waiting for Signal',
          message: `Market conditions neutral. Need RSI below 40 (BUY) or above 60 (SELL).`,
          color: 'bg-gray-100 text-gray-700 border-gray-200',
          icon: '⏸️'
        };
      
      case 'confirming':
        if (canTrade && signalStrength >= 80) {
          return {
            title: 'Ready to Execute',
            message: `Strong ${nextAction.toUpperCase()} signal (${signalStrength}%) confirmed. Will trade automatically.`,
            color: 'bg-green-100 text-green-700 border-green-200',
            icon: '🚀'
          };
        }
        return {
          title: 'Confirming Signal',
          message: `${nextAction.toUpperCase()} signal (${signalStrength}%) being confirmed.`,
          color: 'bg-yellow-100 text-yellow-700 border-yellow-200',
          icon: '⏳'
        };
      
      case 'cooling_down':
        return {
          title: 'Cooldown Period',
          message: `Just traded - waiting 15 minutes before next opportunity.`,
          color: 'bg-blue-100 text-blue-700 border-blue-200',
          icon: '❄️'
        };
      
      default:
        if (canTrade && signalStrength >= 50) {
          return {
            title: 'Ready to Trade',
            message: `${nextAction.toUpperCase()} signal (${signalStrength}%) ready.`,
            color: 'bg-green-100 text-green-700 border-green-200',
            icon: '✅'
          };
        }
        return {
          title: 'Monitoring Market',
          message: `Signal strength ${signalStrength}% - monitoring for opportunities.`,
          color: 'bg-gray-100 text-gray-700 border-gray-200',
          icon: '👁️'
        };
    }
  };

  const statusInfo = getStatusInfo();

  return (
    <div className={`border rounded-lg p-3 ${statusInfo.color} ${className}`}>
      <div className="flex items-start">
        <span className="text-lg mr-3 mt-0.5">{statusInfo.icon}</span>
        <div className="flex-1">
          <div className="text-sm font-medium mb-1">{statusInfo.title}</div>
          <div className="text-xs opacity-90">{statusInfo.message}</div>
          
          {/* Show next action clearly */}
          {nextAction !== 'hold' && (
            <div className="mt-2 text-xs font-medium">
              Next Action: <span className={`${nextAction === 'buy' ? 'text-green-600' : 'text-red-600'}`}>
                {nextAction.toUpperCase()}
              </span>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default TradeBlockingDiagnosis;
