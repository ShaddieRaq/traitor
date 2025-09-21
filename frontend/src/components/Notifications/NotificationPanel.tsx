import React, { useState } from 'react';
import { useNotifications, useMarkAsRead } from '../../hooks/useNotifications';
import type { Notification } from '../../hooks/useNotifications';

const NotificationPanel: React.FC = () => {
  const [filter, setFilter] = useState<'all' | 'unread'>('all');
  const [limit, setLimit] = useState(20);
  
  const { data: notificationsData, isLoading } = useNotifications(
    limit, 
    filter === 'unread'
  );
  const markAsReadMutation = useMarkAsRead();

  const handleMarkAsRead = (notificationId: number) => {
    markAsReadMutation.mutate(notificationId);
  };

  const getPriorityColor = (priority: string) => {
    switch (priority) {
      case 'critical':
        return 'border-l-red-500 bg-red-50';
      case 'high':
        return 'border-l-orange-500 bg-orange-50';
      case 'normal':
        return 'border-l-blue-500 bg-blue-50';
      case 'low':
        return 'border-l-gray-500 bg-gray-50';
      default:
        return 'border-l-gray-500 bg-gray-50';
    }
  };

  const getTypeIcon = (type: string) => {
    switch (type) {
      case 'market_opportunity':
        return { icon: '🎯', label: 'Market Opportunity' };
      case 'system_alert':
        return { icon: '⚠️', label: 'System Alert' };
      case 'trade_alert':
        return { icon: '💰', label: 'Trade Alert' };
      default:
        return { icon: '📢', label: 'Notification' };
    }
  };

  const formatMessage = (message: string) => {
    // Split message into lines and format nicely
    return message.split('\n').map((line, index) => {
      if (line.trim() === '') return null;
      
      // Check if line starts with bullet point or number
      if (line.match(/^\d+\.\s/)) {
        return (
          <div key={index} className="font-medium text-gray-900 mt-2">
            {line}
          </div>
        );
      }
      
      if (line.trim().startsWith('•')) {
        return (
          <div key={index} className="text-sm text-gray-700 ml-4">
            {line}
          </div>
        );
      }
      
      return (
        <div key={index} className="text-sm text-gray-700">
          {line}
        </div>
      );
    }).filter(Boolean);
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="bg-white rounded-lg shadow p-6">
        <div className="flex justify-between items-center mb-4">
          <h2 className="text-2xl font-bold text-gray-900">Notifications</h2>
          <div className="flex items-center space-x-4">
            {/* Filter Toggle */}
            <div className="flex items-center space-x-2">
              <label className="text-sm font-medium text-gray-700">Show:</label>
              <select
                value={filter}
                onChange={(e) => setFilter(e.target.value as 'all' | 'unread')}
                className="border border-gray-300 rounded-md px-3 py-1 text-sm"
              >
                <option value="all">All notifications</option>
                <option value="unread">Unread only</option>
              </select>
            </div>
            
            {/* Limit Control */}
            <div className="flex items-center space-x-2">
              <label className="text-sm font-medium text-gray-700">Show:</label>
              <select
                value={limit}
                onChange={(e) => setLimit(Number(e.target.value))}
                className="border border-gray-300 rounded-md px-3 py-1 text-sm"
              >
                <option value={10}>10 recent</option>
                <option value={20}>20 recent</option>
                <option value={50}>50 recent</option>
              </select>
            </div>
          </div>
        </div>

        {/* Summary Stats */}
        {notificationsData && (
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
            <div className="bg-blue-50 p-4 rounded-lg">
              <div className="text-2xl font-bold text-blue-600">
                {notificationsData.total_count}
              </div>
              <div className="text-sm text-blue-700">Total Notifications</div>
            </div>
            <div className="bg-orange-50 p-4 rounded-lg">
              <div className="text-2xl font-bold text-orange-600">
                {notificationsData.unread_count}
              </div>
              <div className="text-sm text-orange-700">Unread</div>
            </div>
            <div className="bg-green-50 p-4 rounded-lg">
              <div className="text-2xl font-bold text-green-600">
                {notificationsData.notifications.filter(n => n.type === 'market_opportunity').length}
              </div>
              <div className="text-sm text-green-700">Market Opportunities</div>
            </div>
            <div className="bg-purple-50 p-4 rounded-lg">
              <div className="text-2xl font-bold text-purple-600">
                {notificationsData.notifications.filter(n => n.type !== 'market_opportunity').length}
              </div>
              <div className="text-sm text-purple-700">System & Trade Alerts</div>
            </div>
          </div>
        )}
      </div>

      {/* Notifications List */}
      <div className="bg-white rounded-lg shadow overflow-hidden">
        {isLoading ? (
          <div className="p-8 text-center">
            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600 mx-auto"></div>
            <p className="mt-4 text-gray-600">Loading notifications...</p>
          </div>
        ) : !notificationsData?.notifications || notificationsData.notifications.length === 0 ? (
          <div className="p-8 text-center text-gray-500">
            <div className="text-6xl mb-4">🔔</div>
            <h3 className="text-lg font-medium mb-2">No notifications found</h3>
            <p>
              {filter === 'unread' 
                ? 'No unread notifications at the moment'
                : 'Market opportunities and system alerts will appear here'
              }
            </p>
          </div>
        ) : (
          <div className="divide-y divide-gray-200">
            {notificationsData.notifications.map((notification) => {
              const typeInfo = getTypeIcon(notification.type);
              
              return (
                <div
                  key={notification.id}
                  className={`p-6 ${
                    !notification.read 
                      ? `border-l-4 ${getPriorityColor(notification.priority)}` 
                      : 'border-l-4 border-l-transparent'
                  }`}
                >
                  {/* Header */}
                  <div className="flex items-start justify-between mb-3">
                    <div className="flex items-center space-x-3">
                      <span className="text-2xl">{typeInfo.icon}</span>
                      <div>
                        <h3 className="text-lg font-semibold text-gray-900">
                          {notification.title}
                        </h3>
                        <div className="flex items-center space-x-4 mt-1">
                          <span className="text-sm text-gray-500">
                            {typeInfo.label}
                          </span>
                          <span className="text-sm text-gray-500">
                            {notification.time_ago}
                          </span>
                          <span
                            className={`px-2 py-1 text-xs font-medium rounded-full ${
                              notification.priority === 'critical'
                                ? 'bg-red-100 text-red-800'
                                : notification.priority === 'high'
                                ? 'bg-orange-100 text-orange-800'
                                : notification.priority === 'normal'
                                ? 'bg-blue-100 text-blue-800'
                                : 'bg-gray-100 text-gray-800'
                            }`}
                          >
                            {notification.priority.toUpperCase()}
                          </span>
                        </div>
                      </div>
                    </div>
                    
                    <div className="flex items-center space-x-2">
                      {!notification.read && (
                        <>
                          <div className="w-3 h-3 bg-blue-600 rounded-full"></div>
                          <button
                            onClick={() => handleMarkAsRead(notification.id)}
                            className="text-sm text-blue-600 hover:text-blue-800 font-medium"
                            disabled={markAsReadMutation.isPending}
                          >
                            Mark as read
                          </button>
                        </>
                      )}
                    </div>
                  </div>

                  {/* Message Content */}
                  <div className="space-y-1">
                    {formatMessage(notification.message)}
                  </div>
                </div>
              );
            })}
          </div>
        )}
      </div>
    </div>
  );
};

export default NotificationPanel;
