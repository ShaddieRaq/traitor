import { useState, useEffect, useRef } from 'react';

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

export const useWebSocketStable = () => {
  console.log('🔧 useWebSocketStable hook initialized');
  
  const [isConnected, setIsConnected] = useState(false);
  const [dashboardData, setDashboardData] = useState<DashboardData | null>(null);
  const [lastUpdate, setLastUpdate] = useState<Date | null>(null);
  const [error, setError] = useState<string | null>(null);
  
  const ws = useRef<WebSocket | null>(null);
  const hasConnected = useRef(false);
  const mountedRef = useRef(true);

  useEffect(() => {
    // Only connect once when component mounts
    if (hasConnected.current) {
      console.log('⚠️ Hook already connected, skipping');
      return;
    }
    
    console.log('🚀 useWebSocketStable hook starting connection...');
    hasConnected.current = true;
    mountedRef.current = true;
    
    const wsUrl = `ws://localhost:8000/api/v1/ws/dashboard`;
    console.log('Connecting to WebSocket:', wsUrl);
    
    ws.current = new WebSocket(wsUrl);
    
    ws.current.onopen = () => {
      if (!mountedRef.current) return;
      console.log('✅ WebSocket connected successfully');
      setIsConnected(true);
      setError(null);
    };
    
    ws.current.onmessage = (event) => {
      if (!mountedRef.current) return;
      
      try {
        const message = JSON.parse(event.data);
        console.log('📨 WebSocket message received:', message.type);
        
        if (message.type === 'dashboard_init' && message.data) {
          console.log('🎯 Dashboard init data received');
          setDashboardData(message.data);
          setLastUpdate(new Date());
        } else if (message.type === 'temperature_update' && message.data?.bot_temperatures) {
          setDashboardData(prev => prev ? {
            ...prev,
            bot_temperatures: message.data.bot_temperatures,
            timestamp: message.data.timestamp
          } : null);
          setLastUpdate(new Date());
        }
      } catch (err) {
        console.error('Error parsing WebSocket message:', err);
      }
    };
    
    ws.current.onerror = (error) => {
      if (!mountedRef.current) return;
      console.error('❌ WebSocket error:', error);
      setError('WebSocket connection error');
    };
    
    ws.current.onclose = (event) => {
      if (!mountedRef.current) return;
      console.log('🔌 WebSocket disconnected:', event.code, event.reason);
      setIsConnected(false);
      
      // Log more details about the disconnect
      if (event.code !== 1000) {
        console.error('⚠️ Unexpected WebSocket close:', {
          code: event.code,
          reason: event.reason,
          wasClean: event.wasClean
        });
        setError(`Connection closed unexpectedly (code: ${event.code})`);
      }
    };
    
    // Cleanup function
    return () => {
      mountedRef.current = false;
      if (ws.current) {
        console.log('Cleaning up WebSocket connection');
        ws.current.close(1000, 'Component unmount');
        ws.current = null;
      }
    };
  }, []); // Empty dependency array - run only once on mount

  return {
    isConnected,
    dashboardData,
    lastUpdate,
    error,
  };
};
