import { useQuery, useMutation } from '@tanstack/react-query';
import api from '../lib/api';
import { MarketData, ProductTicker, Account } from '../types';

export const useProducts = () => {
  return useQuery({
    queryKey: ['products'],
    queryFn: async () => {
      const response = await api.get('/market/products');
      return response.data.products;
    },
  });
};

export const useTicker = (productId: string) => {
  return useQuery({
    queryKey: ['ticker', productId],
    queryFn: async () => {
      const response = await api.get(`/market/ticker/${productId}`);
      return response.data as ProductTicker;
    },
    refetchInterval: 5000, // Update every 5 seconds
  });
};

export const useCandles = (productId: string, timeframe = '1h', limit = 100) => {
  return useQuery({
    queryKey: ['candles', productId, timeframe, limit],
    queryFn: async () => {
      const response = await api.get(`/market/candles/${productId}`, {
        params: { timeframe, limit },
      });
      return response.data as MarketData[];
    },
  });
};

export const useAccounts = () => {
  return useQuery({
    queryKey: ['accounts'],
    queryFn: async () => {
      const response = await api.get('/market/accounts');
      return response.data as Account[];
    },
  });
};

export const useFetchMarketData = () => {
  return useMutation({
    mutationFn: async ({ productId, timeframe }: { productId: string; timeframe?: string }) => {
      const response = await api.post(`/market/fetch-data/${productId}`, null, {
        params: { timeframe: timeframe || '1h' },
      });
      return response.data;
    },
  });
};
