import { useQuery } from '@tanstack/react-query';

export interface SignalHistoryEntry {
  timestamp: string;
  combined_score: number;
  signal_scores: Record<string, number>;
  temperature: string;
}

export interface BotSignalHistoryData {
  bot_id: number;
  bot_name: string;
  signal_history: SignalHistoryEntry[];
  total_entries: number;
}

export const useBotSignalHistory = (botId: number, limit: number = 20, enabled: boolean = true) => {
  return useQuery<BotSignalHistoryData>({
    queryKey: ['bot-signal-history', botId, limit],
    queryFn: async () => {
      const response = await fetch(`/api/v1/bots/${botId}/signal-history?limit=${limit}`);
      if (!response.ok) {
        throw new Error('Failed to fetch bot signal history');
      }
      return response.json();
    },
    refetchInterval: 30000, // Refresh every 30 seconds (less frequent than live data)
    staleTime: 25000, // Consider data stale after 25 seconds
    enabled: enabled && !!botId, // Only run if enabled and botId is provided
  });
};
