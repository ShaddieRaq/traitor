import React, { useEffect, useRef, useState } from 'react';

interface BotTemperature {
  bot_id: number;
  bot_name: string;
  pair: string;
  status: string;
  temperature: 'hot' | 'warm' | 'cool' | 'frozen' | 'error';
  temperature_emoji: string;
  current_action: string;
  score?: number;
  abs_score?: number;
  distance_to_action?: number;
  next_action?: string;
}

interface DashboardData {
  total_bots: number;
  running_bots: number;
  stopped_bots: number;
  bot_temperatures: BotTemperature[];
  timestamp: string;
}

const WebSocketDashboardSimple: React.FC = () => {
  const [connectionStatus, setConnectionStatus] = useState('Connecting...');
  const [dashboardData, setDashboardData] = useState<DashboardData | null>(null);
  const [updateCounter, setUpdateCounter] = useState(0); // Force re-render trigger
  const wsRef = useRef<WebSocket | null>(null);
  const mountedRef = useRef(true);

  const logMessage = (message: string) => {
    console.log(`[WebSocket] ${message}`);
  };

  useEffect(() => {
    logMessage('🚀 Starting WebSocket connection...');
    
    // Always set mounted to true at the start of this effect
    mountedRef.current = true;
    
    // Prevent double connection in React StrictMode
    if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN) {
      logMessage('⚠️ WebSocket already connected, skipping');
      return;
    }

    if (wsRef.current && wsRef.current.readyState === WebSocket.CONNECTING) {
      logMessage('⚠️ WebSocket already connecting, skipping');
      return;
    }

    const connectWebSocket = () => {
      try {
        logMessage('🔌 Creating WebSocket connection...');
        const ws = new WebSocket('ws://localhost:8000/api/v1/ws/dashboard');
        wsRef.current = ws;

        ws.onopen = () => {
          logMessage('✅ WebSocket connected!');
          // Always update state regardless of mountedRef due to StrictMode issues
          console.log('[WebSocket] Setting connection status to Connected');
          setConnectionStatus('Connected');
          
          // Backend automatically sends dashboard_init, no need to request
          logMessage('⏳ Waiting for automatic dashboard_init message...');
        };

        ws.onmessage = (event) => {
          // Always process messages regardless of mountedRef due to StrictMode issues
          try {
            const message = JSON.parse(event.data);
            logMessage(`📨 Received message: ${message.type}`);
            
            if (message.type === 'dashboard_init' && message.data) {
              logMessage(`📊 Dashboard init received - Total bots: ${message.data.total_bots}, Running: ${message.data.running_bots}, Temperatures: ${message.data.bot_temperatures?.length || 0}`);
              console.log('[WebSocket] Setting dashboard data:', message.data);
              setDashboardData(message.data);
              logMessage(`✅ Dashboard data set successfully`);
            } else if (message.type === 'temperature_update' && message.data) {
              logMessage(`🌡️ Temperature update received - bot_temperatures: ${message.data.bot_temperatures?.length || 0}`);
              console.log('[WebSocket] Temperature update data:', message.data);
              
              // Force a complete re-render by creating entirely new objects
              setDashboardData(prev => {
                if (!prev) {
                  logMessage('❌ No previous dashboard data, cannot update');
                  return prev;
                }
                
                // Create completely new object to force React re-render
                const updated = {
                  total_bots: prev.total_bots,
                  running_bots: prev.running_bots,
                  stopped_bots: prev.stopped_bots,
                  bot_temperatures: message.data.bot_temperatures ? 
                    message.data.bot_temperatures.map((bot: BotTemperature) => ({ ...bot })) : 
                    prev.bot_temperatures.map((bot: BotTemperature) => ({ ...bot })),
                  timestamp: message.data.timestamp || new Date().toISOString()
                };
                
                console.log('[WebSocket] Updated dashboard data:', updated);
                logMessage(`✅ Temperature data updated - ${updated.bot_temperatures?.length || 0} bots`);
                
                // Log the actual score changes for debugging
                if (updated.bot_temperatures && updated.bot_temperatures.length > 0) {
                  const firstBot = updated.bot_temperatures[0];
                  logMessage(`🎯 Bot score: ${firstBot.score} | Temp: ${firstBot.temperature} | Action: ${firstBot.current_action}`);
                }
                
                // Force component re-render
                setUpdateCounter(prev => prev + 1);
                
                return updated;
              });
            } else {
              logMessage(`🤔 Unhandled message type: ${message.type}`);
            }
          } catch (error) {
            logMessage(`❌ Error parsing message: ${error}`);
          }
        };

        ws.onerror = (error) => {
          logMessage(`❌ WebSocket error: ${error}`);
          setConnectionStatus('Error');
        };

        ws.onclose = (event) => {
          logMessage(`🔌 WebSocket closed: ${event.code} ${event.reason}`);
          setConnectionStatus('Disconnected');
        };
        
      } catch (error) {
        logMessage(`❌ Failed to create WebSocket: ${error}`);
        setConnectionStatus('Error');
      }
    };    connectWebSocket();

    // Cleanup on unmount
    return () => {
      logMessage('🧹 Cleaning up WebSocket...');
      mountedRef.current = false;
      if (wsRef.current && wsRef.current.readyState !== WebSocket.CLOSED) {
        wsRef.current.close(1000, 'Component unmount');
        wsRef.current = null;
      }
    };
  }, []); // Empty dependency array

  return (
    <div className="bg-white shadow rounded-lg">
      <div className="px-4 py-5 sm:p-6">
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-lg leading-6 font-medium text-gray-900">
            🌡️ Real-time Bot Temperature Monitor
          </h3>
          <div className="flex items-center space-x-2">
            <div className={`w-2 h-2 rounded-full ${
              connectionStatus === 'Connected' ? 'bg-green-500' : 
              connectionStatus === 'Error' ? 'bg-red-500' : 'bg-yellow-500'
            }`}></div>
            <span className="text-sm text-gray-500">{connectionStatus}</span>
          </div>
        </div>

        {/* Data Display */}
        {dashboardData ? (
          <div className="space-y-4">
            <div className="grid grid-cols-3 gap-4 text-center">
              <div>
                <div className="text-2xl font-bold text-blue-600">{dashboardData.total_bots}</div>
                <div className="text-sm text-gray-500">Total</div>
              </div>
              <div>
                <div className="text-2xl font-bold text-green-600">{dashboardData.running_bots}</div>
                <div className="text-sm text-gray-500">Running</div>
              </div>
              <div>
                <div className="text-2xl font-bold text-gray-600">{dashboardData.stopped_bots}</div>
                <div className="text-sm text-gray-500">Stopped</div>
              </div>
            </div>

            {dashboardData.bot_temperatures.length > 0 && (
              <div className="space-y-2">
                <h4 className="text-sm font-medium text-gray-900">Bot Temperatures</h4>
                {dashboardData.bot_temperatures.map((bot) => (
                  <div key={`${bot.bot_id}-${dashboardData.timestamp}-${bot.score}-${updateCounter}`} className="p-3 bg-gray-50 rounded-lg">{/* Force re-render with changing key */}
                    <div className="flex items-center justify-between mb-2">
                      <div className="flex items-center space-x-3">
                        <span className="text-2xl">{bot.temperature_emoji}</span>
                        <div>
                          <div className="font-medium text-gray-900">{bot.bot_name}</div>
                          <div className="text-sm text-gray-500">{bot.pair}</div>
                        </div>
                      </div>
                      <div className="text-right">
                        <div className="text-sm font-medium text-gray-900">
                          {bot.temperature.toUpperCase()}
                        </div>
                        <div className="text-xs text-gray-500">{bot.current_action}</div>
                      </div>
                    </div>
                    
                    {/* Live Signal Score Display */}
                    <div className="space-y-2">
                      {/* Score Meter */}
                      <div className="bg-white rounded p-2">
                        <div className="flex items-center justify-between mb-1">
                          <span className="text-xs font-semibold text-gray-600">Signal Score</span>
                          <span className={`text-xs font-mono ${
                            bot.score && Math.abs(bot.score) > 0.7 ? 'text-red-600 font-bold' :
                            bot.score && Math.abs(bot.score) > 0.3 ? 'text-orange-600 font-semibold' : 
                            bot.score && Math.abs(bot.score) > 0.1 ? 'text-blue-600' : 'text-gray-500'
                          }`}>
                            {bot.score !== undefined ? bot.score.toFixed(3) : '0.000'}
                          </span>
                        </div>
                        
                        {/* Visual Score Bar */}
                        <div className="relative h-2 bg-gray-200 rounded-full overflow-hidden">
                          <div className="absolute inset-0 flex">
                            {/* Negative side (sell signals) */}
                            <div className="w-1/2 bg-gradient-to-r from-red-400 to-gray-200"></div>
                            {/* Positive side (buy signals) */}
                            <div className="w-1/2 bg-gradient-to-r from-gray-200 to-green-400"></div>
                          </div>
                          
                          {/* Score indicator */}
                          <div 
                            className="absolute top-0 w-1 h-2 bg-black"
                            style={{ 
                              left: `${50 + (bot.score || 0) * 50}%`,
                              transform: 'translateX(-50%)'
                            }}
                          ></div>
                        </div>
                        
                        {/* Scale labels */}
                        <div className="flex justify-between text-xs text-gray-400 mt-1">
                          <span>-1.0</span>
                          <span>0</span>
                          <span>+1.0</span>
                        </div>
                      </div>
                      
                      {/* Detailed Stats */}
                      <div className="grid grid-cols-3 gap-2 text-xs bg-white rounded p-2">
                        <div className="text-center">
                          <div className="font-semibold text-gray-600">Distance</div>
                          <div className="font-mono text-gray-700">
                            {bot.distance_to_action !== undefined ? bot.distance_to_action.toFixed(2) : '0.00'}
                          </div>
                        </div>
                        <div className="text-center">
                          <div className="font-semibold text-gray-600">Next Action</div>
                          <div className="text-gray-700 truncate">
                            {bot.next_action || 'hold'}
                          </div>
                        </div>
                        <div className="text-center">
                          <div className="font-semibold text-gray-600">Strength</div>
                          <div className="font-mono text-gray-700">
                            {bot.abs_score !== undefined ? bot.abs_score.toFixed(2) : '0.00'}
                          </div>
                        </div>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            )}

            {/* Last updated timestamp */}
            {dashboardData.timestamp && (
              <div className="text-xs text-gray-400 text-center mt-4">
                Last updated: {new Date(dashboardData.timestamp).toLocaleTimeString()}
              </div>
            )}
          </div>
        ) : (
          <div className="text-center py-8">
            <div className="text-gray-500">
              {connectionStatus === 'Connected' ? '📊 Waiting for data...' : '🔌 Establishing connection...'}
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default WebSocketDashboardSimple;
