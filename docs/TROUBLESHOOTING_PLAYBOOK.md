# 🚨 Troubleshooting Playbook

Comprehensive debugging guide with proven solutions for common issues encountered during development.

## 🔄 **Real-Time Update Issues**

### **Problem: UI Values Not Updating Automatically**
**Symptoms**: Bot scores and temperatures only update on manual page refresh

#### **Diagnosis Steps**
1. **Check API polling**: Open browser Network tab - should see `/bots/status/summary` requests every 5 seconds
2. **Verify backend freshness**: `curl http://localhost:8000/api/v1/bots/status/summary` - scores should change between calls
3. **Check component keys**: Ensure React components use reactive keys like `key={bot.id}-${bot.current_combined_score}`
4. **Temperature enum mismatch**: Frontend shows 'COLD' but backend returns 'COOL' - fix frontend logic
5. **TanStack Query config**: Ensure `staleTime: 0` and `refetchIntervalInBackground: true`

#### **Common Solutions**
```typescript
// ✅ WORKING: Aggressive polling with reactive keys
const { data: botsStatus } = useBotsStatus(); // Has aggressive polling config
{botsStatus?.map((bot) => (
  <div key={`bot-${bot.id}-${bot.current_combined_score}`}> {/* Reactive key! */}
    <span>{bot.temperature === 'HOT' ? '🔥' : 'COOL' ? '❄️' : '🧊'}</span> {/* Correct enums */}
    <span>{bot.current_combined_score.toFixed(3)}</span>
  </div>
))}
```

#### **Backend Fresh Evaluation Fix**
```python
# ❌ WRONG: Using stale cached database values
temperature = calculate_bot_temperature(bot.current_combined_score)  # Stale!

# ✅ CORRECT: Fresh evaluation with live market data
temp_data = evaluator.calculate_bot_temperature(bot, fresh_market_data)
temperature = temp_data.get('temperature', 'FROZEN')  # Live data!
```

## 🌡️ **Temperature System Issues**

### **Problem: Temperature Values Inconsistent**
**Symptoms**: Frontend shows different temperature than backend returns

#### **Root Causes & Fixes**
1. **Frontend-Backend Enum Mismatch**
   ```typescript
   // ❌ WRONG: Frontend checking for different values than backend returns
   {bot.temperature === 'COLD' ? '❄️' : '🧊'}  // Backend returns 'COOL' not 'COLD'!

   // ✅ CORRECT: Match exact backend enum values
   {bot.temperature === 'HOT' ? '🔥' : 
    bot.temperature === 'WARM' ? '🌡️' : 
    bot.temperature === 'COOL' ? '❄️' : '🧊'}  // COOL not COLD!
   ```

2. **Multiple Temperature Functions**
   ```python
   # ❌ WRONG: Duplicate temperature calculation functions
   def calculate_bot_temperature():  # Don't create duplicates!

   # ✅ CORRECT: Always use centralized utility
   from app.utils.temperature import calculate_bot_temperature
   ```

3. **Unrealistic Thresholds**
   ```python
   # ❌ WRONG: Extreme settings for production
   "rsi": {"period": 2, "buy_threshold": 80, "sell_threshold": 90}  # Too sensitive!

   # ✅ CORRECT: Realistic signal settings
   "rsi": {"period": 14, "buy_threshold": 30, "sell_threshold": 70}
   ```

### **Backend Temperature Values Reference**
- `"HOT"` - Strong signal (abs_score >= 0.08 testing, >= 0.3 production)
- `"WARM"` - Moderate signal (abs_score >= 0.03 testing, >= 0.15 production)  
- `"COOL"` - Weak signal (abs_score >= 0.005 testing, >= 0.05 production)
- `"FROZEN"` - No signal (abs_score < thresholds)

## 🧪 **Test-Related Issues**

### **Problem: Test Bots Persisting After Test Runs**
**Symptoms**: Database accumulates test bots, skewing production data

#### **Solution: Automated Test Cleanup**
```python
# ✅ GOOD: Test cleanup in individual tests
def test_parameter_ranges(self, client):
    created_bot_ids = []
    try:
        # Test logic that creates bots
        if response.status_code == 201:
            created_bot_ids.append(response.json()["id"])
    finally:
        # Always clean up
        for bot_id in created_bot_ids:
            client.delete(f"/api/v1/bots/{bot_id}")

# ✅ GOOD: Session-wide cleanup fixture
@pytest.fixture(scope="session", autouse=True)
def cleanup_test_bots():
    yield  # Let tests run
    # Clean up any remaining test bots by name pattern
    test_bot_names = ["Invalid Position Size Bot", "Invalid Percentage Bot"]
    for bot in get_all_bots():
        if bot.name in test_bot_names:
            delete_bot(bot.id)
```

### **Problem: Slow Coinbase API Tests**
**Symptoms**: Test suite takes 70+ seconds to complete

#### **Solution: Avoid SDK Introspection**
```python
# ❌ WRONG: Triggers slow __getitem__ operation (70+ seconds)
if 'product_id' in coinbase_product_object:

# ✅ CORRECT: Fast attribute checking (<2 seconds)
if hasattr(product, 'product_id'):
```

## 🔧 **Service Management Issues**

### **Problem: Services Won't Start**
**Symptoms**: `./scripts/start.sh` fails or services don't respond

#### **Diagnosis Steps**
1. **Check port conflicts**: `lsof -i :8000`, `lsof -i :3000`, `lsof -i :6379`
2. **Verify virtual environment**: `which python` should show venv path
3. **Check dependencies**: `pip list` in activated venv
4. **Test connectivity**: `curl http://localhost:8000/health`

#### **Common Solutions**
```bash
# Kill conflicting processes
pkill -f "uvicorn app.main:app"
pkill -f "celery"
docker-compose down

# Clean restart
./scripts/stop.sh
./scripts/start.sh

# Manual service check
cd backend && source venv/bin/activate
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### **Problem: Exit Code 127 (Command Not Found)**
**Symptoms**: Commands fail with "command not found"

#### **Root Causes & Fixes**
1. **Wrong directory**: Always `cd` to correct path before commands
2. **Virtual environment not activated**: Run `source venv/bin/activate`
3. **Missing dependencies**: Run `pip install -r requirements.txt`

## 🏦 **Coinbase API Issues**

### **Problem: USD Account Not Found**
**Symptoms**: Portfolio shows crypto but no USD fiat balance

#### **Solution: Use Portfolio Breakdown Method**
```python
# ❌ WRONG: Only returns crypto accounts
accounts = client.get_accounts()

# ✅ CORRECT: Returns both crypto AND fiat accounts  
portfolios = client.get_portfolios()
breakdown = client.get_portfolio_breakdown(portfolio_uuid=portfolios[0]['uuid'])
# USD accounts found in breakdown['spot_positions'] where is_cash=True
```

### **Problem: Rate Limiting or Connection Issues**
**Symptoms**: API calls fail with timeout or rate limit errors

#### **Solutions**
1. **Check API credentials**: Verify `.env` file has correct keys
2. **Rate limit handling**: Implement exponential backoff
3. **Connection pooling**: Use session management for repeated calls

## 📊 **Signal Calculation Issues**

### **Problem: Signal Scores Always Zero**
**Symptoms**: Bot evaluation returns 0.0 scores for all signals

#### **Diagnosis Steps**
1. **Check market data**: Ensure historical data is available
2. **Verify signal parameters**: RSI period, MA periods within data range
3. **Data quality**: Check for NaN values in price data
4. **Signal configuration**: Ensure signals are enabled with proper weights

#### **Common Solutions**
```python
# Check data availability
if len(data) < max(rsi_period, ma_slow_period):
    return {"error": "Insufficient data for signal calculation"}

# Verify signal weights
total_weight = sum(signal.weight for signal in enabled_signals)
if total_weight > 1.0:
    raise ValueError("Total signal weights exceed 1.0")
```

### **Problem: Weight Validation Errors**
**Symptoms**: API rejects bot creation with weight validation errors

#### **Solution: Proper Weight Distribution**
```json
{
  "signal_config": {
    "rsi": {"enabled": true, "weight": 0.5},
    "moving_average": {"enabled": true, "weight": 0.3},
    "macd": {"enabled": true, "weight": 0.2}
  }
}
// Total: 0.5 + 0.3 + 0.2 = 1.0 ✅
```

## 🎨 **Frontend Issues**

### **Problem: Component Not Re-rendering**
**Symptoms**: UI shows stale data even when API returns fresh data

#### **Solutions**
1. **Reactive keys**: Use changing data in component keys
2. **Dependency arrays**: Ensure useEffect/useMemo dependencies are correct
3. **State updates**: Check if state is properly updating

```typescript
// ✅ Force re-render with reactive keys
{bots.map(bot => (
  <BotCard 
    key={`${bot.id}-${bot.current_combined_score}-${bot.temperature}`}
    bot={bot} 
  />
))}
```

### **Problem: TanStack Query Not Refetching**
**Symptoms**: Data doesn't update automatically

#### **Solution: Aggressive Polling Configuration**
```typescript
export const useBotsStatus = () => {
  return useQuery({
    queryKey: ['bots', 'status'],
    queryFn: fetchBotsStatus,
    refetchInterval: 5000,                 // Poll every 5 seconds
    refetchIntervalInBackground: true,     // Continue when tab inactive
    refetchOnWindowFocus: true,            // Refresh when tab focused
    refetchOnMount: true,                  // Fresh data on component mount
    staleTime: 0,                          // Always consider data stale
  });
};
```

## 🐛 **Development Workflow Issues**

### **Problem: Database Schema Changes Not Applied**
**Symptoms**: New columns/tables not appearing

#### **Solutions**
1. **Delete database**: `rm trader.db` (development only)
2. **Restart services**: `./scripts/restart.sh`
3. **Check model definitions**: Verify SQLAlchemy models are correct

### **Problem: Import Errors After Architecture Changes**
**Symptoms**: "ModuleNotFoundError" or "ImportError"

#### **Solutions**
1. **Update all imports**: Use grep to find old import patterns
2. **Clear Python cache**: Remove `__pycache__` directories
3. **Restart Celery workers**: They cache import paths

```bash
# Find and update old imports
grep -r "from.*import.*Signal" backend/app/
# Replace with new patterns
grep -r "from.*import.*Bot" backend/app/
```

## � **CRITICAL: Database Integrity Issues (September 6, 2025)**

### **Problem: Mock Data Contamination**
**Symptoms**: Profitability analysis shows inflated profits, trades without Coinbase order_ids

#### **Emergency Diagnosis**
```bash
# Check for data contamination
sqlite3 backend/trader.db "
SELECT 
    COUNT(*) as total_trades,
    COUNT(CASE WHEN order_id IS NOT NULL AND order_id != '' THEN 1 END) as with_order_id,
    COUNT(CASE WHEN order_id IS NULL OR order_id = '' THEN 1 END) as without_order_id,
    CAST(COUNT(CASE WHEN order_id IS NOT NULL AND order_id != '' THEN 1 END) AS FLOAT) / COUNT(*) * 100 as integrity_percentage
FROM trades;"

# Expected: 100% trades should have order_ids for clean data
# If <100%, you have mock data contamination
```

#### **Emergency Database Cleanup**
```bash
# 1. CRITICAL: Backup before any changes
timestamp=$(date +%Y%m%d_%H%M%S)
cp backend/trader.db "backend/trader_backup_${timestamp}.db"
echo "Backup created: trader_backup_${timestamp}.db"

# 2. Wipe contaminated data
sqlite3 backend/trader.db "DELETE FROM trades;"

# 3. Resync authentic trades from Coinbase
curl -X POST "http://localhost:8000/api/v1/coinbase-sync/sync-coinbase-trades?days_back=30"

# 4. Verify cleanup success
sqlite3 backend/trader.db "SELECT COUNT(*) FROM trades WHERE order_id IS NOT NULL;"
```

### **Problem: Multiple Pending Orders**
**Symptoms**: Bot places multiple orders before previous orders fill

#### **Diagnosis & Fix**
```bash
# Check for multiple pending orders per bot
sqlite3 backend/trader.db "
SELECT bot_id, COUNT(*) as pending_count 
FROM trades 
WHERE status = 'pending' 
GROUP BY bot_id 
HAVING COUNT(*) > 1;"

# Should return no results. If results exist, you have the race condition bug.
```

## �📋 **Quick Diagnostic Commands**

### **System Health Check**
```bash
# Check all services
./scripts/status.sh

# Test API connectivity
curl -s http://localhost:8000/health
curl -s http://localhost:8000/api/v1/bots/

# CRITICAL: Check database integrity
sqlite3 backend/trader.db "SELECT COUNT(*) FROM trades WHERE order_id IS NOT NULL"

# Check for pending order issues
sqlite3 backend/trader.db "SELECT bot_id, COUNT(*) FROM trades WHERE status='pending' GROUP BY bot_id"

# Verify test suite
./scripts/test.sh --unit
```

### **Real-Time System Check**
```bash
# Check live bot status
curl -s "http://localhost:8000/api/v1/bots/status/summary" | python3 -m json.tool

# Monitor API calls (in browser Network tab)
# Should see /bots/status/summary every 5 seconds

# Check frontend polling
open http://localhost:3000
# Values should update automatically without refresh
```

### **Performance Diagnosis**
```bash
# Check response times
time curl -s http://localhost:8000/api/v1/bots/status/summary

# Monitor resource usage
top -p $(pgrep -f uvicorn)

# Check test execution time
time ./scripts/test.sh
```

---
*Troubleshooting Playbook Last Updated: September 3, 2025*  
*Based on real debugging sessions and proven solutions*
