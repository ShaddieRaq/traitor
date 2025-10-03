#!/bin/bash

# UI Layout Debugging Script
# Helps debug UI layout issues, viewport problems, and responsive design

echo "🔍 UI Layout Debugging Tool"
echo "=========================="
echo ""

# Check if frontend is running
if ! curl -s --max-time 3 "http://localhost:3000" > /dev/null; then
    echo "❌ Frontend not running on localhost:3000"
    echo "   Run: cd frontend && npm run dev"
    exit 1
fi

echo "✅ Frontend is running"
echo ""

# Function to test viewport sizes
test_viewport() {
    local width=$1
    local height=$2
    local description=$3
    
    echo "📱 Testing $description ($width x $height)"
    
    # Create a simple test script
    cat > /tmp/viewport_test.js << EOF
document.body.style.width = '${width}px';
document.body.style.height = '${height}px';
window.resizeTo($width, $height);

// Check for overflow issues
const overflowElements = [];
document.querySelectorAll('*').forEach(el => {
    const style = getComputedStyle(el);
    if (style.overflow === 'hidden' && el.scrollHeight > el.clientHeight) {
        overflowElements.push({
            element: el,
            scrollHeight: el.scrollHeight,
            clientHeight: el.clientHeight,
            className: el.className
        });
    }
});

console.log('Viewport: ${width}x${height}');
console.log('Overflow elements found:', overflowElements.length);
overflowElements.forEach(item => {
    console.log('- Overflow detected:', item.className, 
                'Content height:', item.scrollHeight, 
                'Visible height:', item.clientHeight);
});

// Check for bot cards visibility
const botCards = document.querySelectorAll('[class*="bot-card"], [class*="relative group"]');
const visibleCards = Array.from(botCards).filter(card => {
    const rect = card.getBoundingClientRect();
    return rect.top < window.innerHeight && rect.bottom > 0;
});

console.log('Bot cards total:', botCards.length);
console.log('Bot cards visible:', visibleCards.length);
console.log('Bot cards hidden:', botCards.length - visibleCards.length);
EOF

    echo "   - Overflow elements check"
    echo "   - Bot cards visibility check"
    echo "   - Responsive grid behavior"
    echo ""
}

echo "🖥️  Testing Common Viewport Sizes"
echo "================================"

test_viewport 1920 1080 "Desktop Large"
test_viewport 1366 768 "Desktop Standard"
test_viewport 1024 768 "Tablet Landscape"
test_viewport 768 1024 "Tablet Portrait"
test_viewport 375 667 "Mobile Large"
test_viewport 320 568 "Mobile Small"

echo "🔧 CSS Grid Debugging"
echo "===================="
echo ""

# Check for common CSS issues
echo "📋 Common UI Issues to Check:"
echo "   1. max-h-[fixed] values causing cutoff"
echo "   2. overflow-hidden without proper scrolling"
echo "   3. Grid responsiveness at breakpoints"
echo "   4. Temperature group collapse states"
echo "   5. Bot card grid overflow"
echo ""

echo "🛠️  Quick Fixes for Common Issues:"
echo "================================="
echo ""
echo "1. Cards cut off at bottom:"
echo "   - Replace max-h-[fixed] with max-h-[70vh] overflow-y-auto"
echo "   - Example: max-h-[2000px] → max-h-[70vh] overflow-y-auto"
echo ""
echo "2. Content not responsive:"
echo "   - Check grid classes: grid-cols-1 md:grid-cols-2 lg:grid-cols-3"
echo "   - Ensure proper breakpoint usage"
echo ""
echo "3. Collapse animation issues:"
echo "   - Use max-h-0 (collapsed) and max-h-none (expanded)"
echo "   - Add transition-all duration-300 ease-in-out"
echo ""
echo "4. Scroll not working:"
echo "   - Ensure parent container has defined height"
echo "   - Use overflow-y-auto on scrollable container"
echo ""

echo "📊 Live UI Inspection Commands:"
echo "==============================="
echo ""
echo "# Check for hidden bot cards"
echo "curl -s 'http://localhost:8000/api/v1/bots/' | jq 'length'"
echo ""
echo "# Monitor component render times"
echo "# (Run in browser console)"
echo "console.time('BotCards'); setTimeout(() => console.timeEnd('BotCards'), 1000);"
echo ""
echo "# Check responsive grid behavior"
echo "# (Run in browser console)"
echo "document.querySelectorAll('[class*=\"grid\"]').forEach(el => console.log(el.className));"
echo ""

echo "✅ UI Debugging script completed"
echo "💡 Run this script whenever you suspect UI layout issues"
echo "📖 See docs/technical/UI_DEBUGGING_GUIDE.md for detailed troubleshooting"