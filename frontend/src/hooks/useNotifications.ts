import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { api } from '../lib/api';

export interface Notification {
  id: number;
  type: 'market_opportunity' | 'system_alert' | 'trade_alert';
  title: string;
  message: string;
  priority: 'low' | 'normal' | 'high' | 'critical';
  read: boolean;
  created_at: string;
  time_ago: string;
}

export interface NotificationsResponse {
  notifications: Notification[];
  total_count: number;
  unread_count: number;
}

export const useNotifications = (limit: number = 20, unreadOnly: boolean = false) => {
  return useQuery({
    queryKey: ['notifications', limit, unreadOnly],
    queryFn: async () => {
      const params = new URLSearchParams({
        limit: limit.toString(),
        unread_only: unreadOnly.toString()
      });
      const response = await api.get(`/notifications/notifications?${params}`);
      return response.data as NotificationsResponse;
    },
    refetchInterval: 10000, // Refresh every 10 seconds for real-time updates
    refetchIntervalInBackground: true,
    refetchOnWindowFocus: true,
    staleTime: 0
  });
};

export const useUnreadCount = () => {
  return useQuery({
    queryKey: ['notifications', 'unread-count'],
    queryFn: async () => {
      const response = await api.get('/notifications/unread-count');
      return response.data.unread_count as number;
    },
    refetchInterval: 5000, // Check for new notifications every 5 seconds
    refetchIntervalInBackground: true,
    refetchOnWindowFocus: true,
    staleTime: 0
  });
};

export const useMarkAsRead = () => {
  const queryClient = useQueryClient();
  
  return useMutation({
    mutationFn: async (notificationId: number) => {
      const response = await api.post(`/notifications/notifications/${notificationId}/read`);
      return response.data;
    },
    onSuccess: () => {
      // Invalidate and refetch notifications
      queryClient.invalidateQueries({ queryKey: ['notifications'] });
    }
  });
};

export const useTriggerTestNotification = () => {
  const queryClient = useQueryClient();
  
  return useMutation({
    mutationFn: async () => {
      const response = await api.post('/notifications/test');
      return response.data;
    },
    onSuccess: () => {
      // Invalidate and refetch notifications
      queryClient.invalidateQueries({ queryKey: ['notifications'] });
    }
  });
};
