# Bot Evaluator Threshold Patch
# Add this to the _determine_action method in bot_evaluator.py

def _determine_action(self, overall_score: float, bot: Bot) -> str:
    """
    Determine trading action based on overall score and bot-specific thresholds.
    
    Supports per-bot threshold configuration via signal_config.trading_thresholds
    Falls back to default thresholds if not configured.
    """
    
    # Check for bot-specific thresholds in signal_config
    try:
        signal_config = json.loads(bot.signal_config) if isinstance(bot.signal_config, str) else bot.signal_config
        if signal_config and 'trading_thresholds' in signal_config:
            thresholds = signal_config['trading_thresholds']
            buy_threshold = thresholds.get('buy_threshold', -0.1)
            sell_threshold = thresholds.get('sell_threshold', 0.1)
            print(f"🎯 Using custom thresholds for {bot.pair}: buy={buy_threshold}, sell={sell_threshold}")
        else:
            # Default thresholds
            buy_threshold = -0.1
            sell_threshold = 0.1
    except Exception as e:
        # Fallback to default if any error
        buy_threshold = -0.1
        sell_threshold = 0.1
        print(f"⚠️ Error reading thresholds for {bot.pair}, using defaults: {e}")
    
    if overall_score <= buy_threshold:
        return 'buy'
    elif overall_score >= sell_threshold:
        return 'sell'
    else:
        return 'hold'
