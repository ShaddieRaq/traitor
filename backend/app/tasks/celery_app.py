from celery import Celery
from ..core.config import settings

celery_app = Celery(
    "trading_bot",
    broker=settings.redis_url,
    backend=settings.redis_url,
    include=["app.tasks.trading_tasks", "app.tasks.data_tasks"]
)

# Celery configuration
celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    beat_schedule={
        "fetch-market-data": {
            "task": "app.tasks.data_tasks.fetch_market_data_task",
            "schedule": 60.0,  # Every minute
        },
        "fast-trading-loop": {
            "task": "app.tasks.trading_tasks.fast_trading_evaluation",
            "schedule": 0.5,  # Every 500ms
        },
        "update-trade-statuses": {
            "task": "app.tasks.trading_tasks.update_trade_statuses",
            "schedule": 30.0,  # Every 30 seconds
        },
    },
)
