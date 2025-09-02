#!/bin/bash

# Trading Bot Test Runner
# Simple script to run tests in the proper environment

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Get the directory where this script is located
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

echo -e "${BLUE}🧪 Running Trading Bot Tests...${NC}"

# Check if backend virtual environment exists
if [ ! -d "$PROJECT_ROOT/backend/venv" ]; then
    echo -e "${RED}❌ Backend virtual environment not found${NC}"
    echo -e "${YELLOW}💡 Run ./scripts/setup.sh first${NC}"
    exit 1
fi

# Parse command line arguments
TEST_TYPE="all"
VERBOSE=""
COVERAGE=""

while [[ $# -gt 0 ]]; do
    case $1 in
        -v|--verbose)
            VERBOSE="-v"
            shift
            ;;
        -c|--coverage)
            COVERAGE="--cov=app --cov-report=term-missing"
            shift
            ;;
        --unit)
            TEST_TYPE="unit"
            shift
            ;;
        --integration)
            TEST_TYPE="integration"
            shift
            ;;
        --coinbase)
            TEST_TYPE="coinbase"
            shift
            ;;
        -h|--help)
            echo "Usage: $0 [OPTIONS]"
            echo "Options:"
            echo "  -v, --verbose     Verbose output"
            echo "  -c, --coverage    Run with coverage report"
            echo "  --unit           Run only unit tests"
            echo "  --integration    Run only integration tests (requires credentials)"
            echo "  --coinbase       Run only Coinbase connection tests"
            echo "  -h, --help       Show this help"
            exit 0
            ;;
        *)
            echo -e "${RED}Unknown option: $1${NC}"
            exit 1
            ;;
    esac
done

# Change to backend directory and activate virtual environment
cd "$PROJECT_ROOT/backend"
source venv/bin/activate

# Install test dependencies if coverage is requested
if [ -n "$COVERAGE" ]; then
    pip install pytest-cov >/dev/null 2>&1
fi

# Run tests based on type
case $TEST_TYPE in
    "unit")
        echo -e "${BLUE}🔬 Running unit tests...${NC}"
        pytest tests/test_signals.py $VERBOSE $COVERAGE
        ;;
    "integration")
        echo -e "${BLUE}🔗 Running integration tests...${NC}"
        pytest tests/test_api.py tests/test_coinbase.py::TestCoinbaseConnection::test_real_connection $VERBOSE $COVERAGE
        ;;
    "coinbase")
        echo -e "${BLUE}💰 Running Coinbase connection tests...${NC}"
        pytest tests/test_coinbase.py::TestCoinbaseConnection -m integration $VERBOSE
        ;;
    "all")
        echo -e "${BLUE}🧪 Running all tests...${NC}"
        pytest tests/ $VERBOSE $COVERAGE
        ;;
esac

TEST_EXIT_CODE=$?

if [ $TEST_EXIT_CODE -eq 0 ]; then
    echo -e "\n${GREEN}✅ Tests passed!${NC}"
else
    echo -e "\n${RED}❌ Some tests failed!${NC}"
fi

exit $TEST_EXIT_CODE
