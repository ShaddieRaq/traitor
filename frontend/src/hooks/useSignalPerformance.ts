import { useQuery } from '@tanstack/react-query';

interface SignalPerformanceItem {
  type: string;
  accuracy: number;
  signals: number;
  profitCorrelation: number;
  adaptiveWeight: number;
}

interface SignalPerformanceData {
  signalPerformance: SignalPerformanceItem[];
  totalPredictions: number;
  learningActive: boolean;
  avgWeights: {
    rsi: number;
    macd: number;
    moving_average: number;
  };
}

const fetchSignalPerformance = async (): Promise<SignalPerformanceData> => {
  const response = await fetch('/api/v1/intelligence/signal-performance');
  if (!response.ok) {
    throw new Error('Failed to fetch signal performance');
  }
  return response.json();
};

export const useSignalPerformance = () => {
  return useQuery({
    queryKey: ['signal-performance'],
    queryFn: fetchSignalPerformance,
    refetchInterval: 30000, // Refresh every 30 seconds
    staleTime: 25000,
  });
};
