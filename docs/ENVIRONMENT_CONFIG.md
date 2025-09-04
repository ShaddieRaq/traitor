# Environment Configuration for Phase 4.1.2

## Trading Mode Configuration

The trading system now supports configurable trading modes to prevent accidental real money trades during development:

### Test Mode (Default)
```bash
# Default behavior - all trades are mocked
export TRADING_MODE=test
# OR omit the variable entirely
```

### Production Mode  
```bash
# Enable real trading on Coinbase
export TRADING_MODE=production
```

**⚠️ WARNING**: Only set `TRADING_MODE=production` when you're ready for real money trading!

## Environment Variables Summary

| Variable | Default | Description |
|----------|---------|-------------|
| `TRADING_MODE` | `test` | Set to `production` to enable real trades |
| `COINBASE_API_KEY` | Required | Coinbase API credentials |
| `COINBASE_API_SECRET` | Required | Coinbase API credentials |
| `DATABASE_URL` | `sqlite:///./trader.db` | Database connection |
| `REDIS_URL` | `redis://localhost:6379/0` | Redis connection |

## Safety Features

Even in production mode, the following safety limits are enforced:
- Maximum position size: $25 USD
- Maximum daily trades: 10
- Maximum daily loss: $100 USD  
- Minimum temperature: WARM
- Emergency stop functionality

## Mock Trading Indicators

When in test mode, all trade responses include:
```json
{
  "mock": true,
  "order_id": "mock-1234567890-abcd1234"
}
```

Real production trades will not have the `mock` field and will have actual Coinbase order IDs.
