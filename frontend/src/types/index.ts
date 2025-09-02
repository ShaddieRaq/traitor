export interface Signal {
  id: number;
  name: string;
  description: string;
  enabled: boolean;
  weight: number;
  parameters: Record<string, any>;
  created_at: string;
  updated_at?: string;
}

export interface MarketData {
  product_id: string;
  timestamp: string;
  timeframe: string;
  open_price: number;
  high_price: number;
  low_price: number;
  close_price: number;
  volume: number;
}

export interface Trade {
  id: number;
  product_id: string;
  side: string;
  size: number;
  price: number;
  fee: number;
  order_id: string;
  status: string;
  created_at: string;
  filled_at?: string;
}

export interface SignalResult {
  id: number;
  signal_id: number;
  product_id: string;
  timestamp: string;
  score: number;
  action: string;
  confidence: number;
  metadata: Record<string, any>;
}

export interface ProductTicker {
  product_id: string;
  price: number;
  volume_24h: number;
}

export interface Account {
  currency: string;
  available_balance: number;
  hold: number;
}

export interface SignalCreate {
  name: string;
  description: string;
  weight?: number;
  parameters?: Record<string, any>;
}

export interface SignalUpdate {
  name?: string;
  description?: string;
  enabled?: boolean;
  weight?: number;
  parameters?: Record<string, any>;
}
