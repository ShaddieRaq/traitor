# Development Workflow Diagrams

This document contains additional visual diagrams for development workflows and operational procedures.

## Development Environment Setup

### Local Development Flow
```mermaid
flowchart TD
    START[Developer Setup] --> CLONE[Clone Repository]
    CLONE --> ENV[Create .env from .env.example]
    ENV --> BACKEND_SETUP[Backend Setup]
    ENV --> FRONTEND_SETUP[Frontend Setup]
    
    BACKEND_SETUP --> VENV[Create Virtual Environment<br/>python -m venv venv]
    VENV --> ACTIVATE[Activate Environment<br/>source venv/bin/activate]
    ACTIVATE --> PIP[Install Dependencies<br/>pip install -r requirements.txt]
    PIP --> DB_INIT[Initialize Database<br/>SQLAlchemy auto-create]
    
    FRONTEND_SETUP --> NPM[Install Node Packages<br/>npm install]
    NPM --> BUILD_CHECK[Test Build<br/>npm run build]
    
    DB_INIT --> REDIS[Start Redis<br/>docker-compose up redis]
    BUILD_CHECK --> REDIS
    
    REDIS --> DEV_SERVERS[Start Development Servers]
    DEV_SERVERS --> FASTAPI[Backend: uvicorn app.main:app --reload]
    DEV_SERVERS --> REACT_DEV[Frontend: npm run dev]
    DEV_SERVERS --> CELERY_WORKER[Celery: celery -A app.tasks.celery_app worker]
    DEV_SERVERS --> CELERY_BEAT[Scheduler: celery -A app.tasks.celery_app beat]
    
    FASTAPI --> READY[Development Environment Ready]
    REACT_DEV --> READY
    CELERY_WORKER --> READY
    CELERY_BEAT --> READY
    
    style START fill:#e3f2fd
    style READY fill:#c8e6c9
    style REDIS fill:#ffecb3
```

## Testing Strategy

### Test Pyramid
```mermaid
graph TD
    subgraph "Test Levels"
        E2E[End-to-End Tests<br/>Cypress/Playwright<br/>Critical user journeys]
        INTEGRATION[Integration Tests<br/>pytest + TestClient<br/>API endpoint testing]
        UNIT[Unit Tests<br/>pytest + React Testing Library<br/>Individual component/function testing]
    end
    
    subgraph "Test Coverage Areas"
        SIGNAL_TESTS[Signal Logic Tests<br/>RSI calculations<br/>MA crossover detection<br/>Score generation]
        API_TESTS[API Tests<br/>Authentication<br/>CRUD operations<br/>Error handling]
        UI_TESTS[UI Component Tests<br/>Form validation<br/>State updates<br/>User interactions]
        TRADE_TESTS[Trading Flow Tests<br/>Risk management<br/>Order execution<br/>Error scenarios]
    end
    
    E2E --> TRADE_TESTS
    E2E --> UI_TESTS
    INTEGRATION --> API_TESTS
    INTEGRATION --> SIGNAL_TESTS
    UNIT --> SIGNAL_TESTS
    UNIT --> API_TESTS
    UNIT --> UI_TESTS
    
    style E2E fill:#ffcdd2
    style INTEGRATION fill:#fff9c4
    style UNIT fill:#c8e6c9
```

### Continuous Integration Pipeline
```mermaid
sequenceDiagram
    participant Dev as Developer
    participant Git as Git Repository
    participant CI as CI/CD Pipeline
    participant Test as Test Suite
    participant Deploy as Deployment
    
    Dev->>Git: Push code changes
    Git->>CI: Trigger pipeline
    
    Note over CI: Environment Setup
    CI->>CI: Install Python dependencies
    CI->>CI: Install Node dependencies
    CI->>CI: Start test database
    CI->>CI: Start Redis for testing
    
    Note over CI,Test: Testing Phase
    CI->>Test: Run Python unit tests
    Test-->>CI: Backend test results
    CI->>Test: Run React component tests
    Test-->>CI: Frontend test results
    CI->>Test: Run integration tests
    Test-->>CI: API integration results
    CI->>Test: Run E2E tests
    Test-->>CI: End-to-end results
    
    Note over CI,Deploy: Deployment Phase
    alt All Tests Pass
        CI->>Deploy: Deploy to staging
        Deploy-->>CI: Staging deployment success
        CI->>Deploy: Run smoke tests
        Deploy-->>CI: Production ready
    else Tests Fail
        CI->>Dev: Notify test failures
        Dev->>Git: Fix issues and re-push
    end
```

## Monitoring and Observability

### System Health Dashboard
```mermaid
graph TB
    subgraph "Health Monitoring"
        API_HEALTH[API Health<br/>Response times<br/>Error rates<br/>Uptime %]
        DB_HEALTH[Database Health<br/>Connection pool<br/>Query performance<br/>Storage usage]
        CELERY_HEALTH[Celery Health<br/>Worker status<br/>Queue depth<br/>Task failure rate]
        EXTERNAL_HEALTH[External Services<br/>Coinbase API status<br/>WebSocket connection<br/>Rate limit usage]
    end
    
    subgraph "Business Metrics"
        TRADING_METRICS[Trading Performance<br/>Total trades executed<br/>Success rate<br/>P&L tracking]
        SIGNAL_METRICS[Signal Performance<br/>Signal accuracy<br/>Calculation times<br/>Confidence levels]
        USER_METRICS[User Engagement<br/>Dashboard usage<br/>Configuration changes<br/>Alert interactions]
    end
    
    subgraph "Alerting Rules"
        CRITICAL[Critical Alerts<br/>API down > 2min<br/>Trading errors > 5%<br/>Database unreachable]
        WARNING[Warning Alerts<br/>High response times<br/>Queue backup<br/>Low confidence signals]
        INFO[Info Notifications<br/>New trades executed<br/>Configuration changes<br/>System updates]
    end
    
    API_HEALTH --> CRITICAL
    DB_HEALTH --> CRITICAL
    CELERY_HEALTH --> WARNING
    EXTERNAL_HEALTH --> WARNING
    
    TRADING_METRICS --> INFO
    SIGNAL_METRICS --> WARNING
    USER_METRICS --> INFO
    
    style CRITICAL fill:#ffcdd2
    style WARNING fill:#fff9c4
    style INFO fill:#e1f5fe
```

### Error Handling Flow
```mermaid
flowchart TD
    ERROR[Error Occurs] --> TYPE{Error Type?}
    
    TYPE -->|API Error| API_HANDLE[API Error Handler]
    TYPE -->|Database Error| DB_HANDLE[Database Error Handler]
    TYPE -->|Trading Error| TRADE_HANDLE[Trading Error Handler]
    TYPE -->|Signal Error| SIGNAL_HANDLE[Signal Error Handler]
    
    API_HANDLE --> RETRY{Retryable?}
    RETRY -->|Yes| BACKOFF[Exponential Backoff]
    RETRY -->|No| LOG_API[Log Error & Alert]
    BACKOFF --> SUCCESS{Retry Success?}
    SUCCESS -->|Yes| CONTINUE[Continue Operation]
    SUCCESS -->|No| LOG_API
    
    DB_HANDLE --> RECONNECT[Attempt Reconnection]
    RECONNECT --> DB_SUCCESS{Connection Restored?}
    DB_SUCCESS -->|Yes| CONTINUE
    DB_SUCCESS -->|No| FALLBACK[Fallback to Cache]
    
    TRADE_HANDLE --> CANCEL[Cancel Pending Orders]
    CANCEL --> NOTIFY_USER[Notify User]
    NOTIFY_USER --> MANUAL_REVIEW[Flag for Manual Review]
    
    SIGNAL_HANDLE --> SKIP[Skip Current Calculation]
    SKIP --> NEXT_CYCLE[Wait for Next Cycle]
    NEXT_CYCLE --> CONTINUE
    
    LOG_API --> ALERT
    FALLBACK --> ALERT[Send Alert]
    MANUAL_REVIEW --> ALERT
    
    ALERT --> CONTINUE
    
    style ERROR fill:#ffcdd2
    style CONTINUE fill:#c8e6c9
    style ALERT fill:#ff9800
```

## Deployment Architecture

### Production Environment
```mermaid
graph TB
    subgraph "Load Balancer"
        LB[Nginx/Cloudflare<br/>SSL Termination<br/>Rate Limiting]
    end
    
    subgraph "Application Layer"
        API1[FastAPI Instance 1<br/>Gunicorn + Uvicorn]
        API2[FastAPI Instance 2<br/>Gunicorn + Uvicorn]
        STATIC[Static File Server<br/>React Build Assets]
    end
    
    subgraph "Background Processing"
        WORKER1[Celery Worker 1<br/>Signal Processing]
        WORKER2[Celery Worker 2<br/>Data Collection]
        BEAT[Celery Beat<br/>Task Scheduler]
    end
    
    subgraph "Data Layer"
        DB[(PostgreSQL<br/>Production Database)]
        REDIS[(Redis<br/>Task Queue & Cache)]
        BACKUP[(Backup Storage<br/>S3/GCS)]
    end
    
    subgraph "External Services"
        COINBASE[Coinbase API<br/>Trading & Market Data]
        MONITORING[Monitoring<br/>Datadog/New Relic]
        ALERTS[Alerting<br/>PagerDuty/Slack]
    end
    
    LB --> API1
    LB --> API2
    LB --> STATIC
    
    API1 --> DB
    API2 --> DB
    API1 --> REDIS
    API2 --> REDIS
    
    WORKER1 --> DB
    WORKER2 --> DB
    WORKER1 --> REDIS
    WORKER2 --> REDIS
    BEAT --> REDIS
    
    WORKER1 --> COINBASE
    WORKER2 --> COINBASE
    
    DB --> BACKUP
    
    API1 --> MONITORING
    WORKER1 --> MONITORING
    MONITORING --> ALERTS
    
    style LB fill:#e3f2fd
    style DB fill:#fff3e0
    style REDIS fill:#ffecb3
    style COINBASE fill:#f3e5f5
```

### Deployment Pipeline
```mermaid
sequenceDiagram
    participant Dev as Developer
    participant Git as Git Repository
    participant CI as CI/CD System
    participant Stage as Staging Environment
    participant Prod as Production Environment
    participant Monitor as Monitoring
    
    Dev->>Git: Push to main branch
    Git->>CI: Trigger deployment pipeline
    
    Note over CI: Build & Test
    CI->>CI: Run test suite
    CI->>CI: Build Docker images
    CI->>CI: Security scan
    CI->>CI: Performance benchmarks
    
    Note over CI,Stage: Staging Deployment
    CI->>Stage: Deploy to staging
    Stage-->>CI: Health check pass
    CI->>Stage: Run smoke tests
    Stage-->>CI: Smoke tests pass
    
    Note over CI,Prod: Production Deployment
    CI->>Prod: Blue-green deployment
    Prod-->>CI: New version healthy
    CI->>Prod: Switch traffic to new version
    Prod-->>CI: Traffic switch complete
    CI->>Monitor: Update monitoring dashboards
    
    Note over Monitor: Post-deployment
    Monitor->>Monitor: Check key metrics
    Monitor->>CI: Deployment success confirmed
    
    alt Deployment Issues
        Monitor->>CI: Alert on anomalies
        CI->>Prod: Rollback to previous version
        Prod-->>CI: Rollback complete
    end
```

## Security Architecture

### Authentication & Authorization Flow
```mermaid
sequenceDiagram
    participant User as User Browser
    participant Frontend as React App
    participant Backend as FastAPI
    participant Coinbase as Coinbase API
    participant DB as Database
    
    Note over User,DB: Environment Setup
    User->>Frontend: Access trading dashboard
    Frontend->>Backend: Request app configuration
    Backend->>DB: Load signal configurations
    DB-->>Backend: Signal settings
    Backend-->>Frontend: App config + signals
    
    Note over User,DB: Coinbase Authentication
    Backend->>Backend: Load API credentials from env
    Backend->>Coinbase: Authenticate with JWT
    Coinbase-->>Backend: API session established
    
    Note over User,DB: Trading Operations
    Frontend->>Backend: Request market data
    Backend->>Coinbase: GET /api/v3/brokerage/products
    Coinbase-->>Backend: Market data
    Backend-->>Frontend: Formatted market data
    
    Frontend->>Backend: Submit trade signal config
    Backend->>DB: Validate & save configuration
    DB-->>Backend: Configuration saved
    Backend-->>Frontend: Configuration updated
    
    Note over User,DB: Background Trading
    Backend->>Coinbase: Execute trade (when triggered)
    Coinbase-->>Backend: Trade confirmation
    Backend->>DB: Record trade details
    Backend->>Frontend: Notify trade via WebSocket
```

### Data Security Measures
```mermaid
graph TD
    subgraph "Data Protection"
        ENV[Environment Variables<br/>API keys in .env<br/>Never in code/logs]
        ENCRYPT[Data Encryption<br/>Database encryption at rest<br/>TLS for data in transit]
        BACKUP[Secure Backups<br/>Encrypted backup storage<br/>Regular backup testing]
    end
    
    subgraph "Access Control"
        LOCAL[Local Development<br/>Single user system<br/>No user authentication needed]
        API_SEC[API Security<br/>Coinbase JWT authentication<br/>Rate limit compliance]
        NETWORK[Network Security<br/>Firewall rules<br/>VPN for production access]
    end
    
    subgraph "Monitoring"
        AUDIT[Audit Logging<br/>All trade decisions logged<br/>Configuration change tracking]
        ANOMALY[Anomaly Detection<br/>Unusual trading patterns<br/>API usage monitoring]
        INCIDENT[Incident Response<br/>Automated alerts<br/>Emergency stop procedures]
    end
    
    ENV --> API_SEC
    ENCRYPT --> BACKUP
    LOCAL --> NETWORK
    API_SEC --> AUDIT
    NETWORK --> ANOMALY
    AUDIT --> INCIDENT
    
    style ENV fill:#ffcdd2
    style ENCRYPT fill:#c8e6c9
    style AUDIT fill:#fff9c4
```

This comprehensive set of diagrams provides the visual documentation needed to understand and lead the trading bot project from multiple perspectives, focusing on both bot functionality and app responsiveness as requested.
