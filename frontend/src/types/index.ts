// Signal Configuration Types
export interface RSISignalConfig {
  enabled: boolean;
  weight: number;
  period: number;
  buy_threshold: number;
  sell_threshold: number;
}

export interface MovingAverageSignalConfig {
  enabled: boolean;
  weight: number;
  fast_period: number;
  slow_period: number;
}

export interface MACDSignalConfig {
  enabled: boolean;
  weight: number;
  fast_period: number;
  slow_period: number;
  signal_period: number;
}

export interface SignalConfiguration {
  rsi: RSISignalConfig;
  moving_average: MovingAverageSignalConfig;
  macd: MACDSignalConfig;
}

export interface Bot {
  id: number;
  name: string;
  description: string;
  pair: string;
  status: string;
  position_size_usd: number;
  max_positions: number;
  stop_loss_pct: number;
  take_profit_pct: number;
  confirmation_minutes: number;
  trade_step_pct: number;
  cooldown_minutes: number;
  signal_config: SignalConfiguration;
  current_position_size: number;
  current_position_entry_price?: number;
  current_combined_score: number;
  signal_confirmation_start?: string;
  created_at: string;
  updated_at?: string;
  // Optional fields from BotStatus for unified interface
  temperature?: string;
  distance_to_signal?: number;
}

export interface BotCreate {
  name: string;
  description: string;
  pair: string;
  position_size_usd?: number;
  max_positions?: number;
  stop_loss_pct?: number;
  take_profit_pct?: number;
  confirmation_minutes?: number;
  trade_step_pct?: number;
  cooldown_minutes?: number;
  signal_config?: SignalConfiguration;
}

export interface BotUpdate {
  name?: string;
  description?: string;
  status?: string;
  position_size_usd?: number;
  max_positions?: number;
  stop_loss_pct?: number;
  take_profit_pct?: number;
  confirmation_minutes?: number;
  trade_step_pct?: number;
  cooldown_minutes?: number;
  signal_config?: SignalConfiguration;
}

export interface BotStatus {
  id: number;
  name: string;
  pair: string;
  status: string;
  current_combined_score: number;
  current_position_size: number;
  temperature: string;
  distance_to_signal: number;
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
  bot_id: number;
  product_id: string;
  side: string;
  size: number;
  price: number;
  fee: number;
  order_id: string;
  status: string;
  combined_signal_score: number;
  created_at: string;
  filled_at?: string;
}

export interface BotSignalHistory {
  id: number;
  bot_id: number;
  timestamp: string;
  combined_score: number;
  signal_scores: Record<string, any>;
  price: number;
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
