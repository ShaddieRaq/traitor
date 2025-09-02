#!/bin/bash

# Trading Bot Setup Script
# This script sets up the development environment

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Get the directory where this script is located
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

echo -e "${BLUE}🛠️  Trading Bot Development Setup${NC}"
echo -e "${BLUE}=================================${NC}"

# Function to check if command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Check prerequisites
echo -e "\n${BLUE}🔍 Checking prerequisites...${NC}"

if command_exists python3; then
    python_version=$(python3 --version)
    echo -e "   Python3: ${GREEN}✅ ${python_version}${NC}"
else
    echo -e "   Python3: ${RED}❌ Not found${NC}"
    echo -e "${RED}Please install Python 3.8 or higher${NC}"
    exit 1
fi

if command_exists node; then
    node_version=$(node --version)
    echo -e "   Node.js: ${GREEN}✅ ${node_version}${NC}"
else
    echo -e "   Node.js: ${RED}❌ Not found${NC}"
    echo -e "${RED}Please install Node.js 16 or higher${NC}"
    exit 1
fi

if command_exists npm; then
    npm_version=$(npm --version)
    echo -e "   npm: ${GREEN}✅ ${npm_version}${NC}"
else
    echo -e "   npm: ${RED}❌ Not found${NC}"
    echo -e "${RED}npm should be installed with Node.js${NC}"
    exit 1
fi

if command_exists docker; then
    docker_version=$(docker --version)
    echo -e "   Docker: ${GREEN}✅ ${docker_version}${NC}"
else
    echo -e "   Docker: ${RED}❌ Not found${NC}"
    echo -e "${RED}Please install Docker for Redis container${NC}"
    exit 1
fi

if command_exists docker-compose; then
    compose_version=$(docker-compose --version)
    echo -e "   Docker Compose: ${GREEN}✅ ${compose_version}${NC}"
else
    echo -e "   Docker Compose: ${RED}❌ Not found${NC}"
    echo -e "${RED}Please install Docker Compose${NC}"
    exit 1
fi

# Create logs directory
echo -e "\n${BLUE}📁 Creating directories...${NC}"
mkdir -p "$PROJECT_ROOT/logs"
echo -e "   Logs directory: ${GREEN}✅ Created${NC}"

# Setup backend
echo -e "\n${BLUE}🐍 Setting up Python backend...${NC}"
cd "$PROJECT_ROOT/backend"

# Create virtual environment if it doesn't exist
if [ ! -d "venv" ]; then
    echo -e "   Creating virtual environment..."
    python3 -m venv venv
    echo -e "   Virtual environment: ${GREEN}✅ Created${NC}"
else
    echo -e "   Virtual environment: ${GREEN}✅ Already exists${NC}"
fi

# Activate virtual environment and install dependencies
source venv/bin/activate
echo -e "   Installing Python dependencies..."
pip install --upgrade pip
pip install -r requirements.txt
echo -e "   Python dependencies: ${GREEN}✅ Installed${NC}"

# Setup frontend
echo -e "\n${BLUE}⚛️  Setting up React frontend...${NC}"
cd "$PROJECT_ROOT/frontend"

# Install Node.js dependencies
echo -e "   Installing Node.js dependencies..."
npm install
echo -e "   Node.js dependencies: ${GREEN}✅ Installed${NC}"

# Check environment file
echo -e "\n${BLUE}🔧 Checking environment configuration...${NC}"
cd "$PROJECT_ROOT"

if [ -f ".env" ]; then
    echo -e "   Environment file: ${GREEN}✅ Found${NC}"
    
    # Check if required variables exist
    if grep -q "COINBASE_API_KEY" .env && grep -q "COINBASE_API_SECRET" .env; then
        echo -e "   Coinbase credentials: ${GREEN}✅ Configured${NC}"
    else
        echo -e "   Coinbase credentials: ${YELLOW}⚠️  Missing${NC}"
        echo -e "${YELLOW}Please add COINBASE_API_KEY and COINBASE_API_SECRET to .env file${NC}"
    fi
else
    echo -e "   Environment file: ${YELLOW}⚠️  Not found${NC}"
    echo -e "   Creating .env template..."
    cat > .env << 'EOF'
# Coinbase API Configuration
COINBASE_API_KEY=organizations/your-org-id/apiKeys/your-key-id
COINBASE_API_SECRET=-----BEGIN EC PRIVATE KEY-----
YOUR_PRIVATE_KEY_HERE
-----END EC PRIVATE KEY-----

# Database Configuration
DATABASE_URL=sqlite:///./trading_bot.db

# Redis Configuration
REDIS_URL=redis://localhost:6379/0

# Environment
ENVIRONMENT=development
EOF
    echo -e "   Environment template: ${GREEN}✅ Created${NC}"
    echo -e "${YELLOW}Please edit .env file with your Coinbase API credentials${NC}"
fi

# Test Docker setup
echo -e "\n${BLUE}🐳 Testing Docker setup...${NC}"
cd "$PROJECT_ROOT"

if docker-compose config >/dev/null 2>&1; then
    echo -e "   Docker Compose config: ${GREEN}✅ Valid${NC}"
else
    echo -e "   Docker Compose config: ${RED}❌ Invalid${NC}"
    exit 1
fi

# Make scripts executable
echo -e "\n${BLUE}🔧 Setting up management scripts...${NC}"
chmod +x "$SCRIPT_DIR"/*.sh
echo -e "   Script permissions: ${GREEN}✅ Set${NC}"

# Create desktop shortcuts (optional)
echo -e "\n${BLUE}🖥️  Creating desktop shortcuts...${NC}"
if command_exists code; then
    # Create VS Code workspace file
    cat > "$PROJECT_ROOT/trading-bot.code-workspace" << EOF
{
    "folders": [
        {
            "path": "."
        }
    ],
    "settings": {
        "python.defaultInterpreterPath": "./backend/venv/bin/python",
        "python.terminal.activateEnvironment": true,
        "typescript.preferences.include PackageJsonAutoImports": "on",
        "editor.formatOnSave": true,
        "editor.codeActionsOnSave": {
            "source.organizeImports": true
        }
    },
    "extensions": {
        "recommendations": [
            "ms-python.python",
            "ms-python.flake8",
            "ms-python.black-formatter",
            "bradlc.vscode-tailwindcss",
            "ms-vscode.vscode-typescript-next",
            "ms-vscode.vscode-json",
            "ms-toolsai.jupyter"
        ]
    }
}
EOF
    echo -e "   VS Code workspace: ${GREEN}✅ Created${NC}"
else
    echo -e "   VS Code: ${YELLOW}⚠️  Not found, skipping workspace file${NC}"
fi

# Final verification
echo -e "\n${BLUE}🧪 Running setup verification...${NC}"

# Test Python imports
cd "$PROJECT_ROOT/backend"
source venv/bin/activate
if python -c "import fastapi, sqlalchemy, celery, redis; print('All imports successful')" 2>/dev/null; then
    echo -e "   Python imports: ${GREEN}✅ OK${NC}"
else
    echo -e "   Python imports: ${RED}❌ Failed${NC}"
fi

# Test Node.js build
cd "$PROJECT_ROOT/frontend"
if npm run build >/dev/null 2>&1; then
    echo -e "   Frontend build: ${GREEN}✅ OK${NC}"
    # Clean up build
    rm -rf dist
else
    echo -e "   Frontend build: ${RED}❌ Failed${NC}"
fi

echo -e "\n${GREEN}🎉 Setup completed successfully!${NC}"
echo -e "\n${BLUE}📋 Next steps:${NC}"
echo -e "   1. ${YELLOW}Edit .env file with your Coinbase API credentials${NC}"
echo -e "   2. ${YELLOW}Run ./scripts/start.sh to start the application${NC}"
echo -e "   3. ${YELLOW}Open http://localhost:3000 to access the dashboard${NC}"
echo -e "\n${BLUE}🛠️  Management commands:${NC}"
echo -e "   Start: ${YELLOW}./scripts/start.sh${NC}"
echo -e "   Stop: ${YELLOW}./scripts/stop.sh${NC}"
echo -e "   Status: ${YELLOW}./scripts/status.sh${NC}"
echo -e "   Logs: ${YELLOW}./scripts/logs.sh${NC}"
echo -e "   Restart: ${YELLOW}./scripts/restart.sh${NC}"
