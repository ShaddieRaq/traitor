#!/bin/bash

# Test Data Cleanup Script for Trading Bot
# Cleans up test data that accumulates after running tests

set -e

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
BACKEND_DIR="$PROJECT_ROOT/backend"

echo "🧹 Trading Bot Test Data Cleanup"
echo "Project Root: $PROJECT_ROOT"
echo

# Change to backend directory
cd "$BACKEND_DIR"

# Activate virtual environment if it exists
if [ -d "venv" ]; then
    echo "🐍 Activating virtual environment..."
    source venv/bin/activate
fi

# Run the cleanup script
echo "🗑️  Running cleanup script..."
python3 "$PROJECT_ROOT/scripts/cleanup_test_data.py" "$@"

echo
echo "✅ Cleanup script completed!"
