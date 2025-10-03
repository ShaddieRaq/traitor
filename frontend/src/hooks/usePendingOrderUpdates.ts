import { useState, useRef, useEffect } from 'react';

export interface PendingOrderUpdate {
  trade_id: number;
  bot_id: number;
  order_id: string;
  side: string;
  size: number;
  size_usd: number;
  price: number;
  product_id: string;
  status: string;
  created_at: string;
  time_elapsed_seconds: number;
  timestamp: string;
}

export interface OrderStatusChange {
  trade_id: number;
  bot_id: number;
  order_id: string;
  old_status: string;
  new_status: string;
  filled_at: string | null;
  updated_at: string;
  product_id: string;
  side: string;
  size_usd: number;
  timestamp: string;
}

export interface PendingOrderState {
  isConnected: boolean;
  pendingOrders: Map<string, PendingOrderUpdate>; // order_id -> update
  statusChanges: OrderStatusChange[];
  latestStatusChange: OrderStatusChange | null;
}

export const usePendingOrderUpdates = () => {
  const [state, setState] = useState<PendingOrderState>({
    isConnected: false,
    pendingOrders: new Map(),
    statusChanges: [],
    latestStatusChange: null,
  });

  const wsRef = useRef<WebSocket | null>(null);
  const reconnectTimeoutRef = useRef<NodeJS.Timeout | null>(null);

  const connect = () => {
    try {
      // Use the same WebSocket endpoint as trade execution
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
          
          // Handle pending order creation
          if (data.type === 'pending_order_update') {
            const update: PendingOrderUpdate = {
              ...data.data,
              timestamp: data.timestamp,
            };

            setState(prev => {
              const newPendingOrders = new Map(prev.pendingOrders);
              newPendingOrders.set(update.order_id, update);
              
              return {
                ...prev,
                pendingOrders: newPendingOrders,
              };
            });
          }
          
          // Handle order status changes
          else if (data.type === 'order_status_change') {
            const statusChange: OrderStatusChange = {
              ...data.data,
              timestamp: data.timestamp,
            };

            setState(prev => {
              const newPendingOrders = new Map(prev.pendingOrders);
              
              // Remove from pending if order completed/failed
              if (statusChange.new_status === 'completed' || statusChange.new_status === 'failed') {
                newPendingOrders.delete(statusChange.order_id);
              }
              
              // Add to status changes
              const newStatusChanges = [statusChange, ...prev.statusChanges.slice(0, 49)]; // Keep last 50
              
              return {
                ...prev,
                pendingOrders: newPendingOrders,
                statusChanges: newStatusChanges,
                latestStatusChange: statusChange,
              };
            });
          }
        } catch (error) {
          console.error('Error parsing pending order WebSocket message:', error);
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
        console.error('❌ Pending orders WebSocket error:', error);
      };

    } catch (error) {
      console.error('Failed to connect to pending orders WebSocket:', error);
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

  // Helper functions for components
  const getPendingOrdersForBot = (botId: number): PendingOrderUpdate[] => {
    return Array.from(state.pendingOrders.values()).filter(order => order.bot_id === botId);
  };

  const hasPendingOrdersForBot = (botId: number): boolean => {
    return getPendingOrdersForBot(botId).length > 0;
  };

  const getPendingOrderCount = (): number => {
    return state.pendingOrders.size;
  };

  const getRecentStatusChanges = (limit: number = 10): OrderStatusChange[] => {
    return state.statusChanges.slice(0, limit);
  };

  return {
    ...state,
    getPendingOrdersForBot,
    hasPendingOrdersForBot,
    getPendingOrderCount,
    getRecentStatusChanges,
  };
};
