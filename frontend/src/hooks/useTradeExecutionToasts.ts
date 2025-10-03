import { useEffect } from 'react';
import { useTradeExecutionUpdates } from './useTradeExecutionUpdates';
import { useToast } from '../components/ui/Toast';

export const useTradeExecutionToasts = () => {
  const { latestUpdate, updates, isConnected, isExecuting } = useTradeExecutionUpdates();
  const { addToast } = useToast();

  useEffect(() => {
    if (!latestUpdate || !isConnected) return;

    const { status, bot_id, bot_name, side, size_usd, execution_details, error, message } = latestUpdate;

    // Only show toasts for significant events
    switch (status) {
      case 'completed':
        addToast({
          type: 'success',
          title: 'Trade Completed Successfully! 🎉',
          message: execution_details 
            ? `Bot ${bot_id}${bot_name ? ` (${bot_name})` : ''}: ${execution_details.side} $${execution_details.amount.toFixed(2)} @ $${execution_details.price.toFixed(2)}`
            : `Bot ${bot_id}${bot_name ? ` (${bot_name})` : ''}: ${side} ${size_usd ? `$${size_usd.toFixed(2)}` : 'trade'} completed`,
          duration: 8000, // Show longer for success
          actions: [
            {
              label: 'View Details',
              action: () => {
                // Could navigate to trade details or show modal
              },
              style: 'primary'
            }
          ]
        });
        break;

      case 'failed':
        // Determine if this is a price step error for longer display
        const isPriceStepError = error?.includes('Price step requirement') || message?.includes('Price step requirement');
        const duration = isPriceStepError ? 15000 : 10000; // 15 seconds for price step errors, 10 for others
        
        addToast({
          type: 'error',
          title: isPriceStepError ? 'Trade Blocked - Price Movement Required ⚠️' : 'Trade Failed ❌',
          message: error || message || `Bot ${bot_id}${bot_name ? ` (${bot_name})` : ''}: Trade execution failed`,
          duration: duration,
          actions: [
            {
              label: isPriceStepError ? 'Check Price Movement' : 'Retry',
              action: () => {
                if (isPriceStepError) {
                  // Could show price step requirements or market data
                } else {
                  // Could trigger retry logic
                }
              },
              style: 'primary'
            },
            {
              label: 'Check Bot',
              action: () => {
                // Could navigate to bot configuration
              },
              style: 'secondary'
            }
          ]
        });
        break;

      case 'placing_order':
        // Optional: Show info toast for order placement
        addToast({
          type: 'info',
          title: 'Placing Trade Order ⚡',
          message: `Bot ${bot_id}${bot_name ? ` (${bot_name})` : ''}: ${side} ${size_usd ? `$${size_usd.toFixed(2)}` : ''} order being placed...`,
          duration: 3000
        });
        break;

      // Don't show toasts for other intermediate states to avoid spam
      default:
        break;
    }
  }, [latestUpdate, isConnected, addToast]);

  return {
    updates,
    isConnected,
    isExecuting,
    latestUpdate,
  };
};
