import { useState, useEffect, useRef, useCallback } from 'react';

export interface BotTemperature {
  bot_id: number;
  bot_name: string;
  pair: string;
  status: string;
  temperature: 'hot' | 'warm' | 'cool' | 'frozen' | 'error';
  temperature_emoji: string;
  score: number;
  abs_score: number;
  distance_to_action: number;
  next_action: string;
  current_action: string;
  threshold_info: {
    buy_threshold: number;
    sell_threshold: number;
    in_buy_zone: boolean;
    in_sell_zone: boolean;
    in_neutral_zone: boolean;
  };
  confirmation_status: {
    is_confirmed: boolean;
    needs_confirmation: boolean;
    status: string;
    action_being_confirmed: string | null;
    confirmation_start: string | null;
    confirmation_progress: number;
    time_remaining_minutes: number;
  };
  signal_breakdown: Record<string, any>;
}

export interface DashboardData {
  total_bots: number;
  running_bots: number;
  stopped_bots: number;
  bot_temperatures: BotTemperature[];
  timestamp: string;
}

export interface WebSocketMessage {
  type: string;
  data?: any;
}

export const useWebSocketTemperature = () => {
  const [isConnected, setIsConnected] = useState(false);
  const [dashboardData, setDashboardData] = useState<DashboardData | null>(null);
  const [lastUpdate, setLastUpdate] = useState<Date | null>(null);
  const [error, setError] = useState<string | null>(null);
  
  const ws = useRef<WebSocket | null>(null);
  const reconnectTimeout = useRef<NodeJS.Timeout | null>(null);
  const reconnectAttempts = useRef(0);
  const isConnecting = useRef(false);
  const shouldConnect = useRef(true);
  
  const maxReconnectAttempts = 5;
  const baseDelay = 2000; // Start with 2 seconds

  const cleanup = useCallback(() => {
    shouldConnect.current = false;
    isConnecting.current = false;
    
    if (reconnectTimeout.current) {
      clearTimeout(reconnectTimeout.current);
      reconnectTimeout.current = null;
    }
    
    if (ws.current && ws.current.readyState !== WebSocket.CLOSED) {
      ws.current.close(1000, 'Manual disconnect');
      ws.current = null;
    }
  }, []);

  const connect = useCallback(() => {
    // Prevent multiple simultaneous connection attempts
    if (isConnecting.current || !shouldConnect.current) {
      console.log('Skipping connect - already connecting or should not connect');
      return;
    }

    // Don't connect if already connected
    if (ws.current && ws.current.readyState === WebSocket.OPEN) {
      console.log('Skipping connect - already connected');
      return;
    }

    // Clean up existing connection
    if (ws.current && ws.current.readyState !== WebSocket.CLOSED) {
      console.log('Closing existing connection before reconnect');
      ws.current.close();
    }

    isConnecting.current = true;
    setError(null);

    try {
      const wsUrl = `ws://localhost:8000/api/v1/ws/dashboard`;
      console.log('Creating new WebSocket connection to:', wsUrl);
      
      ws.current = new WebSocket(wsUrl);

      ws.current.onopen = () => {
        console.log('WebSocket connected for temperature updates');
        setIsConnected(true);
        setError(null);
        reconnectAttempts.current = 0;
        isConnecting.current = false;
      };

      ws.current.onmessage = (event) => {
        try {
          const message = JSON.parse(event.data);
          
          switch (message.type) {
            case 'dashboard_init':
              if (message.data) {
                setDashboardData(message.data);
                setLastUpdate(new Date());
              }
              break;
              
            case 'temperature_update':
              if (message.data && message.data.bot_temperatures) {
                setDashboardData(prev => prev ? {
                  ...prev,
                  bot_temperatures: message.data.bot_temperatures,
                  timestamp: message.data.timestamp
                } : null);
                setLastUpdate(new Date());
              }
              break;
              
            case 'pong':
              // Handle ping/pong for connection health
              break;
              
            default:
              console.log('Unknown WebSocket message type:', message.type);
          }
        } catch (error) {
          console.error('Error parsing WebSocket message:', error);
        }
      };

      ws.current.onclose = (event) => {
        console.log('WebSocket disconnected:', event.code, event.reason);
        setIsConnected(false);
        isConnecting.current = false;
        
        // Only attempt to reconnect if it wasn't a manual disconnect and we should still be connected
        if (shouldConnect.current && event.code !== 1000 && reconnectAttempts.current < maxReconnectAttempts) {
          const delay = baseDelay * Math.pow(1.5, reconnectAttempts.current);
          reconnectAttempts.current += 1;
          
          console.log(`Attempting to reconnect in ${delay}ms (attempt ${reconnectAttempts.current})`);
          
          reconnectTimeout.current = setTimeout(() => {
            if (shouldConnect.current) {
              connect();
            }
          }, delay);
        } else if (reconnectAttempts.current >= maxReconnectAttempts) {
          setError('Failed to reconnect after multiple attempts');
        }
      };

      ws.current.onerror = (error) => {
        console.error('WebSocket error:', error);
        setError('WebSocket connection error');
        isConnecting.current = false;
      };

    } catch (error) {
      console.error('Error creating WebSocket connection:', error);
      setError('Failed to create WebSocket connection');
      isConnecting.current = false;
    }
  }, []);

  const requestUpdate = useCallback(() => {
    if (ws.current && ws.current.readyState === WebSocket.OPEN) {
      ws.current.send(JSON.stringify({ type: 'request_update' }));
    }
  }, []);

  // Initialize connection once on mount only
  useEffect(() => {
    shouldConnect.current = true;
    connect();

    // Cleanup on unmount
    return () => {
      cleanup();
    };
  }, []); // Empty dependency array - run only once

  return {
    isConnected,
    dashboardData,
    lastUpdate,
    error,
    requestUpdate,
  };
};
