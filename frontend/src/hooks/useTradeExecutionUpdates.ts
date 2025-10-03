import { useEffect, useState, useRef } from 'react';

export interface TradeExecutionUpdate {
  stage: string;
  bot_id: number;
  bot_name?: string;
  side?: string;
  size_usd?: number;
  status: string;
  message: string;
  order_id?: string;
  trade_id?: number;
  error?: string;
  execution_details?: {
    side: string;
    amount: number;
    price: number;
    order_id: string;
  };
  timestamp: string;
}

export interface TradeExecutionState {
  isConnected: boolean;
  updates: TradeExecutionUpdate[];
  latestUpdate: TradeExecutionUpdate | null;
  isExecuting: boolean; // True when any trade is in progress
}

export const useTradeExecutionUpdates = () => {
  const [state, setState] = useState<TradeExecutionState>({
    isConnected: false,
    updates: [],
    latestUpdate: null,
    isExecuting: false,
  });

  const wsRef = useRef<WebSocket | null>(null);
  const reconnectTimeoutRef = useRef<NodeJS.Timeout | null>(null);

  const connect = () => {
    try {
      // Use the backend port for WebSocket connection
      const wsUrl = `ws://localhost:8000/api/v1/ws/trade-execution`;
      
      wsRef.current = new WebSocket(wsUrl);

      wsRef.current.onopen = () => {
        setState(prev => ({ ...prev, isConnected: true }));
        
        // Send ping to keep connection alive
        if (wsRef.current) {
          wsRef.current.send(JSON.stringify({ type: 'ping' }));
        }
      };

      wsRef.current.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data);
          
          if (data.type === 'trade_execution_update') {
            const update: TradeExecutionUpdate = {
              ...data.data,
              timestamp: data.timestamp,
            };

            setState(prev => {
              const newUpdates = [update, ...prev.updates.slice(0, 49)]; // Keep last 50 updates
              const isExecuting = ['starting', 'placing_order', 'order_placed', 'recording'].includes(update.status);
              
              return {
                ...prev,
                updates: newUpdates,
                latestUpdate: update,
                isExecuting: isExecuting || prev.isExecuting,
              };
            });

            // Clear executing state when trade completes or fails
            if (update.status === 'completed' || update.status === 'failed') {
              setTimeout(() => {
                setState(prev => ({ ...prev, isExecuting: false }));
              }, 2000); // Give time for user to see completion message
            }
          }
        } catch (error) {
          console.error('Error parsing WebSocket message:', error);
        }
      };

      wsRef.current.onclose = () => {
        setState(prev => ({ ...prev, isConnected: false }));
        
        // Attempt to reconnect after 3 seconds
        reconnectTimeoutRef.current = setTimeout(() => {
          connect();
        }, 3000);
      };

      wsRef.current.onerror = (error) => {
        console.error('❌ Trade execution WebSocket error:', error);
      };

    } catch (error) {
      console.error('Failed to connect to trade execution WebSocket:', error);
    }
  };

  useEffect(() => {
    connect();

    return () => {
      if (reconnectTimeoutRef.current) {
        clearTimeout(reconnectTimeoutRef.current);
      }
      if (wsRef.current) {
        wsRef.current.close();
      }
    };
  }, []);

  const clearUpdates = () => {
    setState(prev => ({
      ...prev,
      updates: [],
      latestUpdate: null,
    }));
  };

  return {
    ...state,
    clearUpdates,
  };
};
