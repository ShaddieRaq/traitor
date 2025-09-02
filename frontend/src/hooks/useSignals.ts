import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import api from '../lib/api';
import { Signal, SignalCreate, SignalUpdate, SignalResult } from '../types';

// Signals API hooks
export const useSignals = () => {
  return useQuery({
    queryKey: ['signals'],
    queryFn: async () => {
      const response = await api.get('/signals');
      return response.data as Signal[];
    },
  });
};

export const useSignal = (id: number) => {
  return useQuery({
    queryKey: ['signals', id],
    queryFn: async () => {
      const response = await api.get(`/signals/${id}`);
      return response.data as Signal;
    },
  });
};

export const useCreateSignal = () => {
  const queryClient = useQueryClient();
  
  return useMutation({
    mutationFn: async (signal: SignalCreate) => {
      const response = await api.post('/signals', signal);
      return response.data as Signal;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['signals'] });
    },
  });
};

export const useUpdateSignal = () => {
  const queryClient = useQueryClient();
  
  return useMutation({
    mutationFn: async ({ id, signal }: { id: number; signal: SignalUpdate }) => {
      const response = await api.put(`/signals/${id}`, signal);
      return response.data as Signal;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['signals'] });
    },
  });
};

export const useDeleteSignal = () => {
  const queryClient = useQueryClient();
  
  return useMutation({
    mutationFn: async (id: number) => {
      await api.delete(`/signals/${id}`);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['signals'] });
    },
  });
};

export const useToggleSignal = () => {
  const queryClient = useQueryClient();
  
  return useMutation({
    mutationFn: async (id: number) => {
      const response = await api.post(`/signals/${id}/toggle`);
      return response.data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['signals'] });
    },
  });
};

export const useSignalResults = (signalId: number, productId?: string, limit = 100) => {
  return useQuery({
    queryKey: ['signalResults', signalId, productId, limit],
    queryFn: async () => {
      const params = new URLSearchParams();
      if (productId) params.append('product_id', productId);
      params.append('limit', limit.toString());
      
      const response = await api.get(`/signals/${signalId}/results?${params}`);
      return response.data as SignalResult[];
    },
  });
};
