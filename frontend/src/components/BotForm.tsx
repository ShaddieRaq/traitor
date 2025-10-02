import { useState } from 'react';
import { Bot, BotCreate, SignalConfiguration, RSISignalConfig, MovingAverageSignalConfig, MACDSignalConfig } from '../types';
import { useProducts } from '../hooks/useMarket';

interface BotFormProps {
  bot?: Bot | null;
  onSubmit: (data: BotCreate) => void;
  onCancel: () => void;
  isLoading?: boolean;
}

const BotForm: React.FC<BotFormProps> = ({ bot, onSubmit, onCancel, isLoading = false }) => {
  // Load available trading pairs from Coinbase
  const { data: products, isLoading: productsLoading } = useProducts();
  
  // Form state - FIXED: Match actual existing bot values
  const [name, setName] = useState(bot?.name || '');
  const [description, setDescription] = useState(bot?.description || '');
  const [pair, setPair] = useState(bot?.pair || 'BTC-USD');
  const [pairSearch, setPairSearch] = useState('');
  const [positionSizeUsd, setPositionSizeUsd] = useState(bot?.position_size_usd || 25);  // Match $20-25 from existing bots
  const [maxPositions, setMaxPositions] = useState(bot?.max_positions || 30);           // Match 30 from existing bots
  const [stopLossPct, setStopLossPct] = useState(bot?.stop_loss_pct || 15);             // Match 15% from existing bots
  const [takeProfitPct, setTakeProfitPct] = useState(bot?.take_profit_pct || 10);       // Correct - matches existing
  const [tradeStepPct, setTradeStepPct] = useState(bot?.trade_step_pct || 1);           // Close to 0.8-2% range
  const [cooldownMinutes, setCooldownMinutes] = useState(bot?.cooldown_minutes || 30);  // Match 30 min from existing bots

  // Trading thresholds - UPDATED: Match existing bot configuration (±0.1)
  const [buyThreshold, setBuyThreshold] = useState(bot?.signal_config?.trading_thresholds?.buy_threshold || -0.1);
  const [sellThreshold, setSellThreshold] = useState(bot?.signal_config?.trading_thresholds?.sell_threshold || 0.1);

  // Signal configuration states - UPDATED: Match existing bot weights and settings
  const [rsiConfig, setRsiConfig] = useState(() => ({
    enabled: bot?.signal_config?.rsi?.enabled ?? true,  // Default enabled
    weight: bot?.signal_config?.rsi?.weight || 0.4,     // 40% weight
    period: bot?.signal_config?.rsi?.period || 14,
    buy_threshold: bot?.signal_config?.rsi?.buy_threshold || 30,
    sell_threshold: bot?.signal_config?.rsi?.sell_threshold || 70
  }));

  const [maConfig, setMaConfig] = useState<MovingAverageSignalConfig>(() => ({
    enabled: bot?.signal_config?.moving_average?.enabled ?? true,  // Default enabled
    weight: bot?.signal_config?.moving_average?.weight || 0.35,    // 35% weight
    fast_period: bot?.signal_config?.moving_average?.fast_period || 12,
    slow_period: bot?.signal_config?.moving_average?.slow_period || 26
  }));

  const [macdConfig, setMacdConfig] = useState<MACDSignalConfig>(() => ({
    enabled: bot?.signal_config?.macd?.enabled ?? true,  // Default enabled
    weight: bot?.signal_config?.macd?.weight || 0.25,    // 25% weight
    fast_period: bot?.signal_config?.macd?.fast_period || 12,
    slow_period: bot?.signal_config?.macd?.slow_period || 26,
    signal_period: bot?.signal_config?.macd?.signal_period || 9
  }));

  // Validation state
  const [errors, setErrors] = useState<{[key: string]: string}>({});

  // Calculate total weight
  const totalWeight = (rsiConfig.enabled ? rsiConfig.weight : 0) +
                     (maConfig.enabled ? maConfig.weight : 0) +
                     (macdConfig.enabled ? macdConfig.weight : 0);

  const validateForm = (): boolean => {
    const newErrors: {[key: string]: string} = {};

    if (!name.trim()) {
      newErrors.name = 'Bot name is required';
    }

    if (!pair.trim()) {
      newErrors.pair = 'Trading pair is required';
    }

    if (totalWeight > 1) {
      newErrors.weights = 'Total signal weights cannot exceed 1.0';
    }

    if (totalWeight === 0) {
      newErrors.weights = 'At least one signal must be enabled';
    }

    // RSI validation
    if (rsiConfig.enabled) {
      if (rsiConfig.period < 5 || rsiConfig.period > 50) {
        newErrors.rsi = 'RSI period must be between 5 and 50';
      }
      if (rsiConfig.sell_threshold <= rsiConfig.buy_threshold) {
        newErrors.rsi = 'Sell threshold must be higher than buy threshold';
      }
    }

    // MA validation
    if (maConfig.enabled) {
      if (maConfig.fast_period >= maConfig.slow_period) {
        newErrors.ma = 'Fast period must be less than slow period';
      }
    }

    // MACD validation
    if (macdConfig.enabled) {
      if (macdConfig.fast_period >= macdConfig.slow_period) {
        newErrors.macd = 'Fast period must be less than slow period';
      }
    }

    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    
    if (!validateForm()) {
      return;
    }

    const signalConfig: SignalConfiguration = {
      rsi: rsiConfig,
      moving_average: maConfig,
      macd: macdConfig,
      trading_thresholds: {
        buy_threshold: buyThreshold,
        sell_threshold: sellThreshold
      }
    };

    const formData: BotCreate = {
      name: name.trim(),
      description: description.trim() || `${name.trim()} trading bot for ${pair}`,
      pair: pair.trim(),
      signal_config: signalConfig,
      position_size_usd: positionSizeUsd,
      max_positions: maxPositions,
      stop_loss_pct: stopLossPct,
      take_profit_pct: takeProfitPct,
      trade_step_pct: tradeStepPct,
      cooldown_minutes: cooldownMinutes
    };

    onSubmit(formData);
  };

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50">
      <div className="bg-white rounded-lg shadow-xl max-w-4xl w-full max-h-[90vh] overflow-y-auto">
        <div className="px-6 py-4 border-b border-gray-200">
          <h2 className="text-xl font-semibold text-gray-900">
            {bot ? 'Edit Bot' : 'Create New Bot'}
          </h2>
        </div>

        <form onSubmit={handleSubmit} className="p-6 space-y-6">
          {/* Basic Configuration */}
          <div className="space-y-4">
            <h3 className="text-lg font-medium text-gray-900">Basic Configuration</h3>
            
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Bot Name *
                </label>
                <input
                  type="text"
                  value={name}
                  onChange={(e) => setName(e.target.value)}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                  placeholder="e.g., BTC Scalper Bot"
                />
                {errors.name && <p className="mt-1 text-sm text-red-600">{errors.name}</p>}
              </div>
              
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Trading Pair *
                </label>
                <div className="relative">
                  <input
                    type="text"
                    value={pairSearch}
                    onChange={(e) => setPairSearch(e.target.value)}
                    onFocus={() => setPairSearch('')}
                    placeholder="Search trading pairs... (e.g., BTC, ETH, SOL)"
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                    disabled={productsLoading}
                  />
                  {pairSearch && !productsLoading && products && (
                    <div className="absolute z-10 w-full mt-1 bg-white border border-gray-300 rounded-md shadow-lg max-h-60 overflow-y-auto">
                      {products
                        .filter((product: any) => 
                          product.quote_currency_id === 'USD' && 
                          product.status === 'online' && 
                          !product.trading_disabled && 
                          !product.is_disabled &&
                          (product.product_id.toLowerCase().includes(pairSearch.toLowerCase()) ||
                           product.base_name.toLowerCase().includes(pairSearch.toLowerCase()))
                        )
                        .sort((a: any, b: any) => parseFloat(b.approximate_quote_24h_volume || '0') - parseFloat(a.approximate_quote_24h_volume || '0'))
                        .slice(0, 20) // Limit to top 20 results
                        .map((product: any) => (
                          <div
                            key={product.product_id}
                            onClick={() => {
                              setPair(product.product_id);
                              setPairSearch('');
                            }}
                            className="px-3 py-2 hover:bg-gray-100 cursor-pointer border-b border-gray-100 last:border-b-0"
                          >
                            <div className="font-medium">{product.product_id}</div>
                            <div className="text-sm text-gray-600">
                              ${parseFloat(product.price).toLocaleString()} - {product.base_name}
                            </div>
                          </div>
                        ))}
                      {products.filter((product: any) => 
                        product.quote_currency_id === 'USD' && 
                        product.status === 'online' && 
                        !product.trading_disabled && 
                        !product.is_disabled &&
                        (product.product_id.toLowerCase().includes(pairSearch.toLowerCase()) ||
                         product.base_name.toLowerCase().includes(pairSearch.toLowerCase()))
                      ).length === 0 && (
                        <div className="px-3 py-2 text-gray-500 text-center">
                          No trading pairs found for "{pairSearch}"
                        </div>
                      )}
                    </div>
                  )}
                </div>
                <div className="mt-1 text-sm text-gray-600">
                  Selected: <span className="font-medium">{pair}</span>
                </div>
                {errors.pair && <p className="mt-1 text-sm text-red-600">{errors.pair}</p>}
                {productsLoading && (
                  <p className="mt-1 text-xs text-gray-500">Loading available trading pairs from Coinbase...</p>
                )}
              </div>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Description (optional)
              </label>
              <input
                type="text"
                value={description}
                onChange={(e) => setDescription(e.target.value)}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                placeholder="Brief description of this bot's strategy"
              />
            </div>
          </div>

          {/* Weight Distribution Warning */}
          <div className="bg-yellow-50 border border-yellow-200 rounded-md p-4">
            <div className="flex">
              <div className="ml-3">
                <h3 className="text-sm font-medium text-yellow-800">
                  Signal Weight Distribution
                </h3>
                <div className="mt-2 text-sm text-yellow-700">
                  <p>Total Weight: <span className={`font-semibold ${totalWeight > 1 ? 'text-red-600' : 'text-green-600'}`}>
                    {totalWeight.toFixed(2)}/1.00
                  </span></p>
                  <p className="mt-1">Signal weights must total 1.0 or less. Higher weights give more influence to that signal.</p>
                </div>
              </div>
            </div>
            {errors.weights && <p className="mt-2 text-sm text-red-600">{errors.weights}</p>}
          </div>

          {/* Signal Configuration */}
          <div className="space-y-6">
            <h3 className="text-lg font-medium text-gray-900">Signal Configuration</h3>

            {/* RSI Signal */}
            <div className="border border-gray-200 rounded-lg p-4">
              <div className="flex items-center justify-between mb-4">
                <h4 className="font-medium text-gray-900">RSI (Relative Strength Index)</h4>
                <div className="flex items-center">
                  <input
                    type="checkbox"
                    checked={rsiConfig.enabled}
                    onChange={(e) => setRsiConfig(prev => ({ ...prev, enabled: e.target.checked }))}
                    className="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded"
                  />
                  <label className="ml-2 text-sm text-gray-700">Enable</label>
                </div>
              </div>
              
              {rsiConfig.enabled && (
                <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">Weight</label>
                    <input
                      type="number"
                      value={rsiConfig.weight}
                      onChange={(e) => setRsiConfig(prev => ({ ...prev, weight: Number(e.target.value) }))}
                      className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                      min="0"
                      max="1"
                      step="0.01"
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">Period</label>
                    <input
                      type="number"
                      value={rsiConfig.period}
                      onChange={(e) => setRsiConfig(prev => ({ ...prev, period: Number(e.target.value) }))}
                      className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                      min="5"
                      max="50"
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">Buy Threshold (Oversold)</label>
                    <input
                      type="number"
                      value={rsiConfig.buy_threshold}
                      onChange={(e) => setRsiConfig(prev => ({ ...prev, buy_threshold: Number(e.target.value) }))}
                      className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                      min="10"
                      max="80"
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">Sell Threshold (Overbought)</label>
                    <input
                      type="number"
                      value={rsiConfig.sell_threshold}
                      onChange={(e) => setRsiConfig(prev => ({ ...prev, sell_threshold: Number(e.target.value) }))}
                      className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                      min="20"
                      max="90"
                    />
                  </div>
                </div>
              )}
              {errors.rsi && <p className="mt-2 text-sm text-red-600">{errors.rsi}</p>}
            </div>

            {/* Moving Average Signal */}
            <div className="border border-gray-200 rounded-lg p-4">
              <div className="flex items-center justify-between mb-4">
                <h4 className="font-medium text-gray-900">Moving Average Crossover</h4>
                <div className="flex items-center">
                  <input
                    type="checkbox"
                    checked={maConfig.enabled}
                    onChange={(e) => setMaConfig(prev => ({ ...prev, enabled: e.target.checked }))}
                    className="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded"
                  />
                  <label className="ml-2 text-sm text-gray-700">Enable</label>
                </div>
              </div>
              
              {maConfig.enabled && (
                <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">Weight</label>
                    <input
                      type="number"
                      value={maConfig.weight}
                      onChange={(e) => setMaConfig(prev => ({ ...prev, weight: Number(e.target.value) }))}
                      className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                      min="0"
                      max="1"
                      step="0.01"
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">Fast Period</label>
                    <input
                      type="number"
                      value={maConfig.fast_period}
                      onChange={(e) => setMaConfig(prev => ({ ...prev, fast_period: Number(e.target.value) }))}
                      className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                      min="5"
                      max="50"
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">Slow Period</label>
                    <input
                      type="number"
                      value={maConfig.slow_period}
                      onChange={(e) => setMaConfig(prev => ({ ...prev, slow_period: Number(e.target.value) }))}
                      className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                      min="10"
                      max="200"
                    />
                  </div>
                </div>
              )}
              {errors.ma && <p className="mt-2 text-sm text-red-600">{errors.ma}</p>}
            </div>

            {/* MACD Signal */}
            <div className="border border-gray-200 rounded-lg p-4">
              <div className="flex items-center justify-between mb-4">
                <h4 className="font-medium text-gray-900">MACD (Moving Average Convergence Divergence)</h4>
                <div className="flex items-center">
                  <input
                    type="checkbox"
                    checked={macdConfig.enabled}
                    onChange={(e) => setMacdConfig(prev => ({ ...prev, enabled: e.target.checked }))}
                    className="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded"
                  />
                  <label className="ml-2 text-sm text-gray-700">Enable</label>
                </div>
              </div>
              
              {macdConfig.enabled && (
                <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">Weight</label>
                    <input
                      type="number"
                      value={macdConfig.weight}
                      onChange={(e) => setMacdConfig(prev => ({ ...prev, weight: Number(e.target.value) }))}
                      className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                      min="0"
                      max="1"
                      step="0.01"
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">Fast Period</label>
                    <input
                      type="number"
                      value={macdConfig.fast_period}
                      onChange={(e) => setMacdConfig(prev => ({ ...prev, fast_period: Number(e.target.value) }))}
                      className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                      min="5"
                      max="50"
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">Slow Period</label>
                    <input
                      type="number"
                      value={macdConfig.slow_period}
                      onChange={(e) => setMacdConfig(prev => ({ ...prev, slow_period: Number(e.target.value) }))}
                      className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                      min="10"
                      max="100"
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">Signal Period</label>
                    <input
                      type="number"
                      value={macdConfig.signal_period}
                      onChange={(e) => setMacdConfig(prev => ({ ...prev, signal_period: Number(e.target.value) }))}
                      className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                      min="5"
                      max="50"
                    />
                  </div>
                </div>
              )}
              {errors.macd && <p className="mt-2 text-sm text-red-600">{errors.macd}</p>}
            </div>
          </div>

          {/* Risk Management */}
          <div className="space-y-4">
            <h3 className="text-lg font-medium text-gray-900">Risk Management</h3>
            
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Position Size ($)
                </label>
                <input
                  type="number"
                  value={positionSizeUsd}
                  onChange={(e) => setPositionSizeUsd(Number(e.target.value))}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                  min="10"
                  max="10000"
                  step="10"
                />
                <p className="text-xs text-gray-500 mt-1">Amount to invest per trade</p>
              </div>
              
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Max Positions
                </label>
                <input
                  type="number"
                  value={maxPositions}
                  onChange={(e) => setMaxPositions(Number(e.target.value))}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                  min="1"
                  max="100"
                  step="1"
                />
                <p className="text-xs text-gray-500 mt-1">Concurrent positions allowed</p>
              </div>
              
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Trade Step (%)
                </label>
                <input
                  type="number"
                  value={tradeStepPct}
                  onChange={(e) => setTradeStepPct(Number(e.target.value))}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                  min="0.1"
                  max="10"
                  step="0.1"
                />
                <p className="text-xs text-gray-500 mt-1">Min price change between trades</p>
              </div>
            </div>
            
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Stop Loss (%)
                </label>
                <input
                  type="number"
                  value={stopLossPct}
                  onChange={(e) => setStopLossPct(Number(e.target.value))}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                  min="1"
                  max="20"
                  step="0.5"
                />
              </div>
              
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Take Profit (%)
                </label>
                <input
                  type="number"
                  value={takeProfitPct}
                  onChange={(e) => setTakeProfitPct(Number(e.target.value))}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                  min="1"
                  max="50"
                  step="0.5"
                />
              </div>
              
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Cooldown (minutes)
                </label>
                <input
                  type="number"
                  value={cooldownMinutes}
                  onChange={(e) => setCooldownMinutes(Number(e.target.value))}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                  min="1"
                  max="120"
                  step="1"
                />
                <p className="text-xs text-gray-500 mt-1">Wait time between trades</p>
              </div>
            </div>
          </div>

          {/* Trading Thresholds Configuration */}
          <div className="space-y-4">
            <h3 className="text-lg font-medium text-gray-900">Trading Thresholds</h3>
            <div className="bg-blue-50 p-4 rounded-lg border border-blue-200">
              <p className="text-sm text-blue-800 mb-3">
                <strong>Critical:</strong> These thresholds control when trades are actually triggered. 
                Negative values signal BUY opportunities, positive values signal SELL opportunities.
              </p>
              
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Buy Threshold
                  </label>
                  <input
                    type="number"
                    value={buyThreshold}
                    onChange={(e) => setBuyThreshold(Number(e.target.value))}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                    min="-1"
                    max="0"
                    step="0.01"
                  />
                  <p className="text-xs text-gray-500 mt-1">Trigger BUY when signal ≤ this value (e.g., -0.1)</p>
                </div>
                
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Sell Threshold
                  </label>
                  <input
                    type="number"
                    value={sellThreshold}
                    onChange={(e) => setSellThreshold(Number(e.target.value))}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                    min="0"
                    max="1"
                    step="0.01"
                  />
                  <p className="text-xs text-gray-500 mt-1">Trigger SELL when signal ≥ this value (e.g., 0.1)</p>
                </div>
              </div>

              <div className="mt-3">
                <p className="text-xs text-gray-600">
                  <strong>Current System Default:</strong> ±0.1 thresholds (optimized to prevent rate limiting).
                  Lower absolute values = more sensitive trading, higher absolute values = more conservative.
                </p>
              </div>
            </div>
          </div>

          {/* Form Actions */}
          <div className="flex justify-end space-x-4 pt-6 border-t border-gray-200">
            <button
              type="button"
              onClick={onCancel}
              className="px-4 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-md hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={totalWeight > 1 || isLoading}
              className={`px-4 py-2 text-sm font-medium text-white rounded-md focus:outline-none focus:ring-2 focus:ring-offset-2 ${
                totalWeight > 1 || isLoading
                  ? 'bg-gray-400 cursor-not-allowed'
                  : 'bg-blue-600 hover:bg-blue-700 focus:ring-blue-500'
              }`}
            >
              {isLoading ? 'Creating...' : (bot ? 'Update Bot' : 'Create Bot')}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};

export default BotForm;
