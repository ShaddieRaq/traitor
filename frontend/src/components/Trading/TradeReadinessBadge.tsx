import React from 'react';
import { TradeReadiness } from '../../types';

interface TradeReadinessBadgeProps {
  readiness: TradeReadiness;
  className?: string;
}

const TradeReadinessBadge: React.FC<TradeReadinessBadgeProps> = ({ readiness, className = '' }) => {
  const getStatusConfig = (status: string, canTrade: boolean, blockingReason?: string) => {
    // Priority: Check for critical balance issues first
    if (!canTrade && blockingReason?.includes('insufficient_balance')) {
      return {
        color: 'bg-red-100 text-red-800 border-red-300',
        icon: '💰',
        text: 'Insufficient Balance',
        critical: true
      };
    }
    
    if (canTrade && status === 'ready') {
      return {
        color: 'bg-green-100 text-green-800 border-green-200',
        icon: '✅',
        text: 'Ready to Trade'
      };
    }
    
    switch (status) {
      case 'confirming':
        return {
          color: 'bg-yellow-100 text-yellow-800 border-yellow-200',
          icon: '⏳',
          text: 'Confirming Signal'
        };
      case 'ready':
        return {
          color: 'bg-green-100 text-green-800 border-green-200',
          icon: '🎯',
          text: 'Ready'
        };
      case 'cooling_down':
        return {
          color: 'bg-blue-100 text-blue-800 border-blue-200',
          icon: '⏰',
          text: 'Trade Queued'
        };
      case 'no_signal':
        return {
          color: 'bg-gray-100 text-gray-600 border-gray-200',
          icon: '⏸️',
          text: 'No Signal'
        };
      case 'blocked':
        return {
          color: 'bg-orange-100 text-orange-800 border-orange-200',
          icon: '🚫',
          text: 'Blocked'
        };
      default:
        return {
          color: 'bg-gray-100 text-gray-600 border-gray-200',
          icon: '❓',
          text: 'Unknown'
        };
    }
  };

  const getBlockingReasonText = (reason?: string) => {
    if (!reason) return null;
    
    // Handle insufficient balance with detailed message
    if (reason.startsWith('insufficient_balance:')) {
      const message = reason.replace('insufficient_balance: ', '');
      return `💰 ${message}`;
    }
    
    switch (reason) {
      case 'cooldown':
        return 'Trade queued - waiting for cooldown'; // Simplified since timer is shown separately
      case 'no_signal':
        return 'Waiting for signal';
      case 'safety_limit':
        return 'Safety limit reached';
      case 'bot_stopped':
        return 'Bot is stopped';
      case 'awaiting_confirmation':
        return 'Awaiting confirmation';
      case 'cannot_get_price':
        return '⚠️ Cannot get market price';
      case 'balance_check_error':
        return '⚠️ Balance check failed';
      default:
        return reason; // Show the raw reason if it's not in our predefined list
    }
  };

  const config = getStatusConfig(readiness.status, readiness.can_trade, readiness.blocking_reason);
  const blockingText = getBlockingReasonText(readiness.blocking_reason);

  return (
    <div className={`${className}`}>
      <div className={`inline-flex items-center px-2.5 py-1 rounded-md text-xs font-medium border ${config.color}`}>
        <span className="mr-1">{config.icon}</span>
        {config.text}
      </div>
      
      {blockingText && (
        <div className={`text-xs mt-1 ${
          blockingText.includes('💰') 
            ? 'text-red-600 font-medium bg-red-50 px-2 py-1 rounded border border-red-200' 
            : 'text-gray-500'
        }`}>
          {blockingText}
        </div>
      )}
      
      {readiness.can_trade && readiness.status === 'ready' && (
        <div className="flex items-center mt-1">
          <div className="w-1 h-1 bg-green-400 rounded-full animate-pulse mr-1"></div>
          <span className="text-xs text-green-600 font-medium">
            Trade will execute automatically
          </span>
        </div>
      )}
    </div>
  );
};

export default TradeReadinessBadge;
