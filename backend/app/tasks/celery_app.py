from celery import Celery
from ..core.config import settings

celery_app = Celery(
    "trading_bot",
    broker=settings.redis_url,
    backend=settings.redis_url,
    include=[
        "app.tasks.trading_tasks", 
        "app.tasks.data_tasks", 
        "app.tasks.market_analysis_tasks", 
        "app.tasks.new_pair_tasks",
        "app.tasks.market_data_tasks"  # NEW: Phase 7 Market Data Service
    ]
)

# Celery configuration
celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    beat_schedule={
        # PHASE 7: Market Data Service - TEMPORARILY DISABLED to prevent rate limiting
        # "market-data-refresh": {
        #     "task": "app.tasks.market_data_tasks.refresh_all_market_data",
        #     "schedule": 120.0,  # Every 2 minutes - DISABLED due to 41 API calls per run
        # },
        # "products-list-refresh": {
        #     "task": "app.tasks.market_data_tasks.refresh_products_list",
        #     "schedule": 300.0,  # Every 5 minutes - DISABLED (products change rarely)
        # },
        "market-data-stats": {
            "task": "app.tasks.market_data_tasks.cache_stats_logger",
            "schedule": 60.0,  # Every minute - monitor cache performance
        },
        # Existing tasks - TEMPORARILY DISABLED to prevent rate limiting
        # "fetch-market-data": {
        #     "task": "app.tasks.data_tasks.fetch_market_data_task",
        #     "schedule": 300.0,  # Every 5 minutes - DISABLED
        # },
        # "fast-trading-loop": {
        #     "task": "app.tasks.trading_tasks.fast_trading_evaluation", 
        #     "schedule": 600.0,  # Every 10 minutes - DISABLED
        # },
        "update-trade-statuses": {
            "task": "app.tasks.trading_tasks.update_trade_statuses",
            "schedule": 120.0,  # Every 2 minutes - reduced from 30s to prevent rate limiting
        },
        # Auto bot scanner disabled - user prefers Market Analysis tab
        # "periodic-market-scan": {
        #     "task": "app.tasks.market_analysis_tasks.periodic_market_scan",
        #     "schedule": 3600.0,  # Every hour - comprehensive market analysis
        # },
        # "market-opportunity-alert": {
        #     "task": "app.tasks.market_analysis_tasks.market_opportunity_alert",
        #     "schedule": 1800.0,  # Every 30 minutes - check for exceptional opportunities
        # },
        "scan-for-new-pairs": {
            "task": "app.tasks.new_pair_tasks.scan_for_new_pairs_task",
            "schedule": 7200.0,  # Every 2 hours - detect newly listed pairs
        },
    },
)
