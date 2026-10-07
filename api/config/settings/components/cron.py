"""
Cron job configuration using django-celery-beat.
"""

from celery.schedules import crontab


CELERY_BEAT_SCHEDULE = {
    "redis-health-check": {
        "task": "core.tasks.cache_maintenance.redis_health_check",
        "schedule": 300.0,
        "options": {
            "expires": 600,
        },
    },
    "cache-health-monitoring": {
        "task": "core.tasks.cache_maintenance.cache_health_monitoring",
        "schedule": 900.0,
        "options": {
            "expires": 1200,
        },
    },
    "invalidate-stats-cache": {
        "task": "core.tasks.cache_maintenance.invalidate_stats_cache",
        "schedule": crontab(minute=0),
        "options": {
            "expires": 3600,
        },
    },
    "cache-cleanup": {
        "task": "core.tasks.cache_maintenance.cache_cleanup",
        "schedule": crontab(hour=2, minute=0),
        "options": {
            "expires": 3600,
        },
    },
    "cache-warmup": {
        "task": "core.tasks.cache_maintenance.cache_warmup",
        "schedule": crontab(hour=2, minute=30),
        "options": {
            "expires": 3600,
        },
    },
}


CELERY_BEAT_SCHEDULER = "django_celery_beat.schedulers:DatabaseScheduler"
CELERY_BEAT_SCHEDULE_FILENAME = "celerybeat-schedule"
