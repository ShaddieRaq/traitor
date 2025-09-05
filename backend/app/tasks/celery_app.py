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
        # Temporarily disabled to fix performance issue
        # "evaluate-signals": {
        #     "task": "app.tasks.trading_tasks.evaluate_bot_signals",
        #     "schedule": 300.0,  # Every 5 minutes
        # },
    },
)
