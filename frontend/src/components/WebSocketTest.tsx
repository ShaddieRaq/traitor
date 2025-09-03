import React, { useState, useEffect } from 'react';

const WebSocketTest: React.FC = () => {
  const [connectionStatus, setConnectionStatus] = useState('Disconnected');
  const [messages, setMessages] = useState<string[]>([]);
  const [ws, setWs] = useState<WebSocket | null>(null);

  const connect = () => {
    if (ws && ws.readyState !== WebSocket.CLOSED) {
      ws.close();
    }

    const wsUrl = 'ws://localhost:8000/api/v1/ws/dashboard';
    console.log('Connecting to:', wsUrl);
    
    const newWs = new WebSocket(wsUrl);
    
    newWs.onopen = () => {
      console.log('Connected!');
      setConnectionStatus('Connected');
      setMessages(prev => [...prev, 'Connected successfully']);
    };
    
    newWs.onmessage = (event) => {
      console.log('Message received:', event.data);
      setMessages(prev => [...prev, `Received: ${event.data}`]);
    };
    
    newWs.onclose = (event) => {
      console.log('Disconnected:', event.code, event.reason);
      setConnectionStatus('Disconnected');
      setMessages(prev => [...prev, `Disconnected: ${event.code} - ${event.reason}`]);
    };
    
    newWs.onerror = (error) => {
      console.error('WebSocket error:', error);
      setConnectionStatus('Error');
      setMessages(prev => [...prev, 'Error occurred']);
    };
    
    setWs(newWs);
  };

  const sendMessage = () => {
    if (ws && ws.readyState === WebSocket.OPEN) {
      const message = JSON.stringify({ type: 'request_update' });
      ws.send(message);
      setMessages(prev => [...prev, `Sent: ${message}`]);
    }
  };

  const disconnect = () => {
    if (ws) {
      ws.close(1000, 'Manual disconnect');
      setWs(null);
    }
  };

  useEffect(() => {
    return () => {
      if (ws) {
        ws.close();
      }
    };
  }, [ws]);

  return (
    <div className="p-6 max-w-4xl mx-auto">
      <h2 className="text-2xl font-bold mb-4">WebSocket Connection Test</h2>
      
      <div className="mb-4">
        <div className={`inline-block px-3 py-1 rounded-full text-sm font-medium ${
          connectionStatus === 'Connected' ? 'bg-green-100 text-green-800' :
          connectionStatus === 'Error' ? 'bg-red-100 text-red-800' :
          'bg-gray-100 text-gray-800'
        }`}>
          Status: {connectionStatus}
        </div>
      </div>

      <div className="space-x-2 mb-4">
        <button
          onClick={connect}
          className="px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700"
        >
          Connect
        </button>
        <button
          onClick={sendMessage}
          disabled={connectionStatus !== 'Connected'}
          className="px-4 py-2 bg-green-600 text-white rounded hover:bg-green-700 disabled:bg-gray-400"
        >
          Request Update
        </button>
        <button
          onClick={disconnect}
          className="px-4 py-2 bg-red-600 text-white rounded hover:bg-red-700"
        >
          Disconnect
        </button>
        <button
          onClick={() => setMessages([])}
          className="px-4 py-2 bg-gray-600 text-white rounded hover:bg-gray-700"
        >
          Clear Log
        </button>
      </div>

      <div className="bg-gray-50 p-4 rounded-lg">
        <h3 className="text-lg font-semibold mb-2">Connection Log</h3>
        <div className="max-h-96 overflow-y-auto space-y-1">
          {messages.length === 0 ? (
            <p className="text-gray-500">No messages yet</p>
          ) : (
            messages.map((message, index) => (
              <div key={index} className="text-sm font-mono bg-white p-2 rounded border">
                <span className="text-gray-500">[{new Date().toLocaleTimeString()}]</span> {message}
              </div>
            ))
          )}
        </div>
      </div>
    </div>
  );
};

export default WebSocketTest;
