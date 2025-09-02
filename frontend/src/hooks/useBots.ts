import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import api from '../lib/api';
import { Bot, BotCreate, BotUpdate, BotStatus } from '../types';

// Bots API hooks
export const useBots = () => {
  return useQuery({
    queryKey: ['bots'],
    queryFn: async () => {
      const response = await api.get('/bots');
      return response.data as Bot[];
    },
  });
};

export const useBot = (id: number) => {
  return useQuery({
    queryKey: ['bots', id],
    queryFn: async () => {
      const response = await api.get(`/bots/${id}`);
      return response.data as Bot;
    },
  });
};

export const useBotsStatus = () => {
  return useQuery({
    queryKey: ['bots', 'status'],
    queryFn: async () => {
      const response = await api.get('/bots/status/summary');
      return response.data as BotStatus[];
    },
    refetchInterval: 5000, // Refresh every 5 seconds for real-time updates
  });
};

export const useCreateBot = () => {
  const queryClient = useQueryClient();
  
  return useMutation({
    mutationFn: async (bot: BotCreate) => {
      const response = await api.post('/bots', bot);
      return response.data as Bot;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['bots'] });
    },
  });
};

export const useUpdateBot = () => {
  const queryClient = useQueryClient();
  
  return useMutation({
    mutationFn: async ({ id, bot }: { id: number; bot: BotUpdate }) => {
      const response = await api.put(`/bots/${id}`, bot);
      return response.data as Bot;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['bots'] });
    },
  });
};

export const useDeleteBot = () => {
  const queryClient = useQueryClient();
  
  return useMutation({
    mutationFn: async (id: number) => {
      const response = await api.delete(`/bots/${id}`);
      return response.data;
    },
    onMutate: async (id: number) => {
      // Cancel any outgoing refetches (so they don't overwrite our optimistic update)
      await queryClient.cancelQueries({ queryKey: ['bots'] });

      // Snapshot the previous value
      const previousBots = queryClient.getQueryData(['bots']);

      // Optimistically update to remove the bot
      queryClient.setQueryData(['bots'], (old: Bot[] | undefined) => {
        return old ? old.filter(bot => bot.id !== id) : [];
      });

      // Return a context object with the snapshotted value
      return { previousBots };
    },
    onError: (_err, _id, context) => {
      // If the mutation fails, use the context to roll back
      if (context?.previousBots) {
        queryClient.setQueryData(['bots'], context.previousBots);
      }
    },
    onSuccess: () => {
      // Invalidate and refetch to ensure consistency
      queryClient.invalidateQueries({ queryKey: ['bots'] });
      queryClient.invalidateQueries({ queryKey: ['bots', 'status'] });
    },
  });
};

export const useStartBot = () => {
  const queryClient = useQueryClient();
  
  return useMutation({
    mutationFn: async (id: number) => {
      const response = await api.post(`/bots/${id}/start`);
      return response.data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['bots'] });
    },
  });
};

export const useStopBot = () => {
  const queryClient = useQueryClient();
  
  return useMutation({
    mutationFn: async (id: number) => {
      const response = await api.post(`/bots/${id}/stop`);
      return response.data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['bots'] });
    },
  });
};

export const useStopAllBots = () => {
  const queryClient = useQueryClient();
  
  return useMutation({
    mutationFn: async () => {
      const response = await api.post('/bots/stop-all');
      return response.data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['bots'] });
    },
  });
};
