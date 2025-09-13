import { useQuery } from '@tanstack/react-query';

// Position tracking interfaces to match the new backend API
export interface Position {
  product_id: string;
  current_quantity: number;
  average_cost_basis: number;
  unrealized_pnl: number;
  realized_pnl: number;
  total_pnl: number;
  total_fees: number;
  trade_count: number;
  buy_count: number;
  sell_count: number;
  position_status: string;
}

export interface PositionSummary {
  total_realized_pnl: number;
  total_unrealized_pnl: number;
  total_pnl: number;
  total_fees: number;
  total_trades: number;
  open_positions_count: number;
  closed_positions_count: number;
  products_traded: number;
}

export interface PositionResponse {
  positions: Position[];
  summary: PositionSummary;
}

// Hook to get all positions using the new position tracking API
export const usePositionTracking = () => {
  return useQuery<Position[]>({
    queryKey: ['position-tracking'],
    queryFn: async () => {
      const response = await fetch('/api/v1/positions/');
      if (!response.ok) {
        throw new Error('Failed to fetch position tracking data');
      }
      return response.json();
    },
    refetchInterval: 15000, // Refresh every 15 seconds for real-time data
    refetchIntervalInBackground: true,
    staleTime: 5000, // Consider data stale after 5 seconds for trading data
  });
};

// Hook to get position data for a specific product
export const useProductPosition = (productId: string) => {
  const { data: positions, isLoading, error } = usePositionTracking();
  
  const position = positions?.find(
    (p: Position) => p.product_id === productId
  );

  return {
    position,
    isLoading,
    error,
    hasPosition: !!position
  };
};

// Hook to get position summary totals
export const usePositionSummary = () => {
  return useQuery<PositionSummary>({
    queryKey: ['position-summary'],
    queryFn: async () => {
      const response = await fetch('/api/v1/positions/summary');
      if (!response.ok) {
        throw new Error('Failed to fetch position summary');
      }
      return response.json();
    },
    refetchInterval: 15000,
    refetchIntervalInBackground: true,
    staleTime: 5000,
  });
};
