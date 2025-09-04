# Current Class Diagram

*Auto-generated from codebase - always current*

```mermaid
classDiagram
    class BotSignalEvaluator {
        -__init__(db, enable_confirmation)
        +evaluate_bot(bot, market_data)
        -_create_signal_instance(signal_name, config)
        -_check_signal_confirmation(bot, current_action, current_score)
        -_determine_action(overall_score, bot)
        ... (7 more methods)
    }
    BotSignalEvaluator : backend/app/services/bot_evaluator.py
    class TradeExecutionError {
    }
    TradeExecutionError : backend/app/api/schemas.py
    class TradingService {
        -__init__(db)
        +execute_trade(bot_id, side, size_usd, current_temperature)
        -_get_bot(bot_id)
        -_get_bot_temperature(bot)
        -_validate_trade_safety(bot, side, size_usd, current_temperature)
        ... (7 more methods)
    }
    TradingService : backend/app/services/trading_service.py
    class CoinbaseService {
        -__init__()
        -_initialize_client()
        -_initialize_websocket()
        -_handle_ws_message(message)
        -_trigger_bot_evaluations(product_id, ticker_data)
        ... (10 more methods)
    }
    CoinbaseService : backend/app/services/coinbase_service.py
    class StreamingBotEvaluator {
        -__init__(db)
        +evaluate_bots_on_ticker_update(product_id, ticker_data)
        -_get_market_data_for_evaluation(product_id)
        -_broadcast_evaluation_results(product_id, results)
        +get_active_products()
        ... (1 more methods)
    }
    StreamingBotEvaluator : backend/app/services/streaming_bot_evaluator.py
    class TradingSafetyLimits {
    }
    TradingSafetyLimits : backend/app/services/trading_safety.py
    class TradingSafetyService {
        -__init__(db)
        +validate_trade_request(bot, side, size_usd, current_temperature)
        -_check_position_size(size_usd)
        -_check_daily_trade_limits(bot)
        -_check_daily_loss_limits()
        ... (5 more methods)
    }
    TradingSafetyService : backend/app/services/trading_safety.py
    class RSISignal {
        -__init__(period, oversold, overbought)
        +calculate(data)
        +get_required_periods()
    }
    RSISignal : backend/app/services/signals/technical.py
    class MovingAverageSignal {
        -__init__(fast_period, slow_period)
        +calculate(data)
        +get_required_periods()
    }
    MovingAverageSignal : backend/app/services/signals/technical.py
    class MACDSignal {
        -__init__(fast_period, slow_period, signal_period)
        +calculate(data)
        +get_required_periods()
    }
    MACDSignal : backend/app/services/signals/technical.py
    class BaseSignal {
        -__init__(name, description, weight)
        +calculate(data)*
        +get_required_periods()*
        +is_valid_data(data)
        +to_dict()
    }
    BaseSignal : backend/app/services/signals/base.py
    class Bot {
    }
    Bot : backend/app/models/models.py
    class BotSignalHistory {
    }
    BotSignalHistory : backend/app/models/models.py
    class MarketData {
    }
    MarketData : backend/app/models/models.py
    class Trade {
    }
    Trade : backend/app/models/models.py
    class RSISignalConfig {
        +sell_must_be_greater_than_buy(cls, v, info)
    }
    RSISignalConfig : backend/app/api/schemas.py
    class MovingAverageSignalConfig {
        +slow_must_be_greater_than_fast(cls, v, info)
    }
    MovingAverageSignalConfig : backend/app/api/schemas.py
    class MACDSignalConfig {
        +slow_must_be_greater_than_fast(cls, v, info)
    }
    MACDSignalConfig : backend/app/api/schemas.py
    class SignalConfigurationSchema {
        +validate_total_weight()
    }
    SignalConfigurationSchema : backend/app/api/schemas.py
    class BotCreate {
        +validate_signal_config(cls, v)
    }
    BotCreate : backend/app/api/schemas.py
    class BotUpdate {
        +validate_signal_config(cls, v)
    }
    BotUpdate : backend/app/api/schemas.py
    class BotResponse {
    }
    BotResponse : backend/app/api/schemas.py
    class BotStatusResponse {
    }
    BotStatusResponse : backend/app/api/schemas.py
    class MarketDataResponse {
    }
    MarketDataResponse : backend/app/api/schemas.py
    class TradeResponse {
    }
    TradeResponse : backend/app/api/schemas.py
    class BotSignalHistoryResponse {
    }
    BotSignalHistoryResponse : backend/app/api/schemas.py
    class ProductTickerResponse {
    }
    ProductTickerResponse : backend/app/api/schemas.py
    class AccountResponse {
    }
    AccountResponse : backend/app/api/schemas.py
    class TradeValidationRequest {
        +validate_side(cls, v)
    }
    TradeValidationRequest : backend/app/api/schemas.py
    class SafetyCheckResult {
    }
    SafetyCheckResult : backend/app/api/schemas.py
    class TradeValidationResponse {
    }
    TradeValidationResponse : backend/app/api/schemas.py
    class SafetyLimitsStatus {
    }
    SafetyLimitsStatus : backend/app/api/schemas.py
    class SafetyCurrentStatus {
    }
    SafetyCurrentStatus : backend/app/api/schemas.py
    class SafetyStatusResponse {
    }
    SafetyStatusResponse : backend/app/api/schemas.py
    class TradeExecutionRequest {
        +validate_side(cls, v)
    }
    TradeExecutionRequest : backend/app/api/schemas.py
    class TradeExecutionResponse {
    }
    TradeExecutionResponse : backend/app/api/schemas.py
    class TradeStatusResponse {
    }
    TradeStatusResponse : backend/app/api/schemas.py
    class ConnectionManager {
        -__init__()
        +disconnect(websocket)
    }
    ConnectionManager : backend/app/api/websocket.py
    class Settings {
    }
    Settings : backend/app/core/config.py
    class Config {
    }
    Config : backend/app/core/config.py
    BaseSignal <|-- RSISignal
    BaseSignal <|-- MovingAverageSignal
    BaseSignal <|-- MACDSignal
```
