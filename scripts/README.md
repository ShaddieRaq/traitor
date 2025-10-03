# Trading Bot Management Scripts

This directory contains shell scripts to manage the Trading Bot application lifecycle.

## Quick Start

```bash
# First time setup
./scripts/setup.sh

# Start all services
./scripts/start.sh

# Check status
./scripts/status.sh

# View logs
./scripts/logs.sh

# Stop all services
./scripts/stop.sh
```

## Testing Workflows

### 🧪 `test-workflow.sh` ⭐ **COMPREHENSIVE TESTING**
**Complete validation workflow for system changes**
- **Step 1**: Restart application and verify services
- **Step 2**: Run all tests (must pass 100%, no skips)
- **Step 3**: Sync trades with Coinbase  
- **Step 4**: Validate positions against actual holdings
- **Final**: System health check and readiness confirmation

```bash
# Run full testing workflow after any changes
./scripts/test-workflow.sh
```

### ⚡ `quick-test.sh` 
**Rapid validation for development iterations**
- Quick restart, test run, sync check, position validation
- Abbreviated output for fast feedback during development

```bash
# Quick validation during active development
./scripts/quick-test.sh
```

## UI Debugging Tools (October 2025)

### 🔍 `debug-ui.sh` **NEW**
**Debug UI layout issues and responsive design problems**
- Viewport size testing for mobile/tablet/desktop
- Overflow element detection and bot card visibility checks
- Quick fix recommendations for common CSS issues

```bash
# Debug UI layout problems
./scripts/debug-ui.sh
```

### ⚡ `monitor-frontend-performance.sh` **NEW**
**Monitor frontend performance and identify bottlenecks**
- API endpoint response time testing
- Component render time analysis and memory usage monitoring
- Browser console performance test scripts

```bash
# Monitor frontend performance
./scripts/monitor-frontend-performance.sh
```

### 🔧 `position-reconcile.sh`
**Position tracking validation and correction**
- Check for discrepancies between bot tracking and Coinbase holdings
- Automatically fix position mismatches
- Essential for production trading safety

```bash
./scripts/position-reconcile.sh check   # Check only
./scripts/position-reconcile.sh fix     # Fix discrepancies  
./scripts/position-reconcile.sh both    # Check then fix with confirmation
```

## Scripts Overview

### 🛠️ `setup.sh`
**Initial development environment setup**
- Checks prerequisites (Python, Node.js, Docker)
- Creates virtual environment and installs dependencies
- Creates logs directory and environment template
- Sets up VS Code workspace file
- Makes all scripts executable

```bash
./scripts/setup.sh
```

### 🚀 `start.sh`
**Start all application services**
- Starts Redis Docker container
- Starts FastAPI backend with health checks
- Starts React frontend development server
- Starts Celery worker and beat scheduler
- Verifies all services are running properly
- Runs in background with PID tracking

```bash
./scripts/start.sh
```

### 🛑 `stop.sh`
**Stop all application services gracefully**
- Stops all services using PID files
- Fallback process killing by pattern matching
- Stops Redis Docker container
- Cleans up old log files (older than 7 days)
- Verifies all services stopped

```bash
./scripts/stop.sh
```

### 📊 `status.sh`
**Check application status and health**
- Shows Docker container status
- Checks port availability (6379, 8000, 3000)
- Verifies service processes via PID files
- Tests API endpoint health
- Shows recent log activity
- Displays system resource usage

```bash
./scripts/status.sh
```

### 🔄 `restart.sh`
**Restart all services**
- Runs stop.sh then start.sh
- Includes 5-second wait between stop and start

```bash
./scripts/restart.sh
```

### 📝 `logs.sh`
**View and manage log files**
- View logs for specific services or all
- Follow logs in real-time
- Clear all log files
- Customizable number of lines to show

```bash
# View last 50 lines of all logs
./scripts/logs.sh

# Follow backend logs in real-time
./scripts/logs.sh -f backend

# Show last 100 lines of worker logs
./scripts/logs.sh -n 100 worker

# Clear all log files
./scripts/logs.sh --clear
```

#### Log Services:
- `backend` - FastAPI backend logs
- `frontend` - React frontend logs  
- `worker` - Celery worker logs
- `beat` - Celery beat scheduler logs
- `all` - All services (default)

#### Log Options:
- `-f, --follow` - Follow log output (like tail -f)
- `-n, --lines N` - Show last N lines (default: 50)
- `-c, --clear` - Clear all log files
- `-h, --help` - Show help

### 🧹 `cleanup.sh`
**Clean up test data after running tests**
- Removes all test bots and their associated data
- Cleans up orphaned signal history and trades
- Removes old signal history to prevent accumulation
- Safe dry-run mode available

```bash
# Preview what would be cleaned up (recommended first)
./scripts/cleanup.sh --dry-run

# Actually clean up test data
./scripts/cleanup.sh

# Keep more signal history (default is 24 hours)
./scripts/cleanup.sh --keep-hours=48
```

#### Cleanup Features:
- **Test Bot Removal**: Deletes bots with 'test' in their name
- **Associated Data**: Removes trades and signal history for deleted bots  
- **Orphaned Data**: Cleans up data for non-existent bots
- **Signal History**: Removes old entries to prevent database bloat
- **Dry Run**: Preview changes before applying them

## File Structure

```
scripts/
├── setup.sh      # One-time environment setup
├── start.sh      # Start all services
├── stop.sh       # Stop all services  
├── restart.sh    # Restart all services
├── status.sh     # Check service status
├── logs.sh       # View/manage logs
└── README.md     # This file
```

## Log Files

All services log to `logs/` directory:
- `backend.log` - FastAPI application logs
- `frontend.log` - React development server logs
- `celery-worker.log` - Background task processing logs
- `celery-beat.log` - Task scheduling logs
- `*.pid` - Process ID files for service management

## Process Management

Scripts use PID files in `logs/` directory to track running services:
- `backend.pid` - FastAPI server process ID
- `frontend.pid` - React dev server process ID  
- `celery-worker.pid` - Celery worker process ID
- `celery-beat.pid` - Celery beat process ID

## Error Handling

All scripts include:
- ✅ Exit on error (`set -e`)
- ✅ Prerequisite checking
- ✅ Service health verification
- ✅ Graceful shutdown with timeouts
- ✅ Fallback process cleanup
- ✅ Colored output for status indication

## Troubleshooting

### Common Issues

**Permission denied when running scripts:**
```bash
chmod +x scripts/*.sh
```

**Services won't start:**
1. Check if ports are already in use: `./scripts/status.sh`
2. Verify prerequisites: `./scripts/setup.sh`
3. Check logs: `./scripts/logs.sh`

**API endpoints not responding:**
1. Verify backend is running: `./scripts/status.sh`
2. Check backend logs: `./scripts/logs.sh backend`
3. Verify environment configuration in `.env`

**Docker Redis issues:**
```bash
docker-compose down
docker-compose up redis -d
```

**Virtual environment issues:**
```bash
cd backend
rm -rf venv
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### Manual Debugging

If scripts fail, you can run services manually:

```bash
# Redis
docker-compose up redis -d

# Backend  
cd backend && source venv/bin/activate
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Frontend
cd frontend
npm run dev

# Celery Worker
cd backend && source venv/bin/activate  
celery -A app.tasks.celery_app worker --loglevel=info

# Celery Beat
cd backend && source venv/bin/activate
celery -A app.tasks.celery_app beat --loglevel=info
```

## Development Workflow

### Daily Development
```bash
# Start your development session
./scripts/start.sh

# Check everything is running
./scripts/status.sh

# Follow logs during development
./scripts/logs.sh -f all

# End your session
./scripts/stop.sh
```

### Making Changes
```bash
# Restart after backend changes
./scripts/restart.sh

# Just restart backend after Python changes
./scripts/stop.sh
./scripts/start.sh

# View specific service logs
./scripts/logs.sh backend
```

### Debugging Issues
```bash
# Check service health
./scripts/status.sh

# View recent logs
./scripts/logs.sh

# Clear logs and restart
./scripts/logs.sh --clear
./scripts/restart.sh
```
