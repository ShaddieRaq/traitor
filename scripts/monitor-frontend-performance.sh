#!/bin/bash

# Performance Monitoring Script for Frontend Components
# Monitors rendering performance, memory usage, and identifies bottlenecks

echo "⚡ Frontend Performance Monitor"
echo "==============================="
echo ""

# Check if tools are available
check_dependency() {
    if ! command -v $1 &> /dev/null; then
        echo "❌ $1 is required but not installed"
        return 1
    fi
    echo "✅ $1 is available"
}

echo "🔍 Checking dependencies..."
check_dependency "curl" || exit 1
check_dependency "jq" || echo "⚠️  jq not available - JSON parsing will be limited"

# Check frontend status
if ! curl -s --max-time 3 "http://localhost:3000" > /dev/null; then
    echo "❌ Frontend not running on localhost:3000"
    echo "   Start with: cd frontend && npm run dev"
    exit 1
fi

echo "✅ Frontend is running"
echo ""

# Monitor API response times
echo "📊 API Performance Monitoring"
echo "============================="

monitor_api() {
    local endpoint=$1
    local description=$2
    
    echo "Testing $description..."
    
    # Measure response time
    start_time=$(date +%s%N)
    response=$(curl -s --max-time 10 "http://localhost:8000$endpoint")
    end_time=$(date +%s%N)
    
    duration=$(( (end_time - start_time) / 1000000 )) # Convert to milliseconds
    
    if [ $? -eq 0 ]; then
        echo "✅ $description: ${duration}ms"
        
        # Check response size if jq is available
        if command -v jq &> /dev/null && [[ $response == {* ]]; then
            size=$(echo "$response" | jq 'length // 0')
            echo "   📦 Response size: $size items"
        fi
    else
        echo "❌ $description: Failed (timeout or error)"
    fi
}

# Test critical API endpoints
monitor_api "/api/v1/bots/" "Bot list"
monitor_api "/api/v1/bots/status/enhanced" "Enhanced bot status"
monitor_api "/api/v1/raw-trades/pnl-by-product" "P&L data"
monitor_api "/api/v1/cache/stats" "Cache statistics"

echo ""
echo "🏎️  Component Performance Analysis"
echo "=================================="

# Create performance test script for browser console
cat > /tmp/frontend_perf_test.js << 'EOF'
// Frontend Performance Testing Script
console.log('🚀 Starting performance analysis...');

// Measure bot card rendering
const measureBotCardRender = () => {
    const startTime = performance.now();
    
    // Count bot cards
    const botCards = document.querySelectorAll('[class*="relative group"], [class*="bot-card"]');
    const endTime = performance.now();
    
    console.log(`🤖 Bot cards found: ${botCards.length}`);
    console.log(`⏱️  Card query time: ${(endTime - startTime).toFixed(2)}ms`);
    
    // Check for performance issues
    if (botCards.length > 30 && (endTime - startTime) > 50) {
        console.warn('⚠️  High card count with slow query - consider virtualization');
    }
    
    return { count: botCards.length, queryTime: endTime - startTime };
};

// Measure scroll performance
const measureScrollPerformance = () => {
    const scrollContainers = document.querySelectorAll('[class*="overflow-y-auto"]');
    console.log(`📜 Scroll containers found: ${scrollContainers.length}`);
    
    scrollContainers.forEach((container, index) => {
        const hasLargeContent = container.scrollHeight > container.clientHeight * 2;
        const childCount = container.children.length;
        
        console.log(`📦 Container ${index + 1}:`);
        console.log(`   Content height: ${container.scrollHeight}px`);
        console.log(`   Visible height: ${container.clientHeight}px`);
        console.log(`   Child elements: ${childCount}`);
        console.log(`   Needs scrolling: ${hasLargeContent ? 'Yes' : 'No'}`);
        
        if (childCount > 50) {
            console.warn('⚠️  High element count - consider pagination or virtualization');
        }
    });
};

// Check for memory leaks
const checkMemoryUsage = () => {
    if (performance.memory) {
        const memory = performance.memory;
        console.log('💾 Memory usage:');
        console.log(`   Used: ${(memory.usedJSHeapSize / 1024 / 1024).toFixed(2)} MB`);
        console.log(`   Total: ${(memory.totalJSHeapSize / 1024 / 1024).toFixed(2)} MB`);
        console.log(`   Limit: ${(memory.jsHeapSizeLimit / 1024 / 1024).toFixed(2)} MB`);
        
        const usage = (memory.usedJSHeapSize / memory.jsHeapSizeLimit) * 100;
        if (usage > 80) {
            console.warn('⚠️  High memory usage detected');
        }
    } else {
        console.log('💾 Memory API not available');
    }
};

// Run all tests
measureBotCardRender();
measureScrollPerformance();
checkMemoryUsage();

// Performance recommendations
console.log('');
console.log('📋 Performance Recommendations:');
console.log('================================');
console.log('1. Use max-h-[70vh] overflow-y-auto for large lists');
console.log('2. Implement pagination for >100 items');
console.log('3. Use React.memo for expensive components');
console.log('4. Monitor TanStack Query cache size');
console.log('5. Use intersection observer for lazy loading');

EOF

echo "📋 Browser Console Performance Test:"
echo "===================================="
echo ""
echo "Copy and paste this into your browser console on the dashboard:"
echo ""
cat /tmp/frontend_perf_test.js
echo ""

echo "🔧 Performance Optimization Tips"
echo "==============================="
echo ""
echo "1. For large bot lists (>50 bots):"
echo "   - Use max-h-[70vh] overflow-y-auto"
echo "   - Consider react-window for virtualization"
echo "   - Implement pagination or grouping"
echo ""
echo "2. For API response times >500ms:"
echo "   - Check backend logs: tail -f logs/backend.log"
echo "   - Monitor cache hit rates: curl -s localhost:8000/api/v1/cache/stats"
echo "   - Consider request debouncing"
echo ""
echo "3. For high memory usage:"
echo "   - Check for memory leaks in React components"
echo "   - Optimize TanStack Query cache settings"
echo "   - Use React DevTools Profiler"
echo ""

echo "📊 Real-time Monitoring Commands"
echo "==============================="
echo ""
echo "# Monitor API response times continuously"
echo "watch -n 5 'curl -s --max-time 3 \"http://localhost:8000/api/v1/bots/\" | jq \"length\"'"
echo ""
echo "# Check cache performance"
echo "watch -n 10 'curl -s \"http://localhost:8000/api/v1/cache/stats\" | jq \".hit_rate\"'"
echo ""
echo "# Monitor frontend bundle size"
echo "cd frontend && npm run build && du -sh dist/"
echo ""

echo "✅ Performance monitoring setup complete"
echo "🎯 Focus areas: API response times, scroll performance, memory usage"