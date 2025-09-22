"""
Cron job configuration using django-celery-beat.
"""

from celery.schedules import crontab
from celery import Celery


CELERY_BEAT_SCHEDULE = {
    "daily-stats-generation": {
        "task": "apps.stats.cron_tasks.generate_daily_stats",
        "schedule": crontab(hour=0, minute=0),
        "options": {
            "expires": 3600,
        },
    },
    "weekly-stats-generation": {
        "task": "apps.stats.cron_tasks.generate_weekly_stats",
        "schedule": crontab(hour=0, minute=30, day_of_week=0),
        "options": {
            "expires": 7200,
        },
    },
    "monthly-stats-generation": {
        "task": "apps.stats.cron_tasks.generate_monthly_stats",
        "schedule": crontab(hour=1, minute=0, day_of_month=1),
        "options": {
            "expires": 10800,
        },
    },
    "google-analytics-sync-daily": {
        "task": "apps.stats.services.enhanced_analytics.sync_google_analytics_data",
        "schedule": crontab(hour=2, minute=0),
        "kwargs": {"days": 7},
        "options": {
            "expires": 7200,
        },
    },
    "google-analytics-sync-weekly": {
        "task": "apps.stats.services.enhanced_analytics.sync_google_analytics_data",
        "schedule": crontab(hour=3, minute=0, day_of_week=0),
        "kwargs": {"days": 30},
        "options": {
            "expires": 10800,
        },
    },
    "update-pending-video-statuses": {
        "task": "apps.video_ai.tasks.update_pending_video_statuses",
        "schedule": 300.0,
        "options": {
            "expires": 600,
        },
    },
    "stats-ext-nightly-recompute": {
        "task": "apps.stats_ext.tasks.recompute_stats",
        "schedule": 1800.0,
        "options": {
            "expires": 1800,
        },
    },
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
    "check-bnpl-status": {
        "task": "apps.payment.tasks.bnpl_polling.check_bnpl_status",
        "schedule": crontab(minute="*/10"),
        "options": {
            "expires": 900,
        },
    },
    "test-daily-stats-every-day": {
        "task": "apps.stats.cron_tasks.generate_daily_stats",
        "schedule": crontab(hour="*/6"),
        "enabled": False,
        "options": {
            "expires": 30,
        },
    },
    "test-ga-sync-every-60-seconds": {
        "task": "apps.stats.services.enhanced_analytics.sync_google_analytics_data",
        "schedule": crontab(hour="*/12"),
        "enabled": False,
        "kwargs": {"days": 1},
        "options": {
            "expires": 120,
        },
    },
}


CELERY_BEAT_SCHEDULER = (
    "core.schedulers.patched_database_scheduler:PatchedDatabaseScheduler"
)
CELERY_BEAT_SCHEDULE_FILENAME = "celerybeat-schedule"
