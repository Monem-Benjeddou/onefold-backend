"""
Complete cron system test suite summary.

This test runs a quick validation of all critical cron functionality
to ensure the cron system is properly configured and working.
"""

from django.test import TestCase
from ..components.cron import CELERY_BEAT_SCHEDULE, CELERY_BEAT_SCHEDULER


class CronCompleteSummaryTest(TestCase):
    """Complete cron system validation summary."""

    def test_cron_system_is_configured(self):
        """Test that the cron system is properly configured."""

        self.assertIsNotNone(CELERY_BEAT_SCHEDULE)
        self.assertGreater(len(CELERY_BEAT_SCHEDULE), 0)

        self.assertEqual(
            CELERY_BEAT_SCHEDULER,
            "core.schedulers.patched_database_scheduler:PatchedDatabaseScheduler",
        )

    def test_all_production_tasks_present(self):
        """Test that all expected production tasks are present."""
        expected_tasks = [
            "daily-stats-generation",
            "weekly-stats-generation",
            "monthly-stats-generation",
            "google-analytics-sync-daily",
            "google-analytics-sync-weekly",
            "update-pending-video-statuses",
            "stats-ext-nightly-recompute",
            "redis-health-check",
            "cache-health-monitoring",
            "invalidate-stats-cache",
            "cache-cleanup",
            "cache-warmup",
            "check-bnpl-status",
        ]

        for task in expected_tasks:
            self.assertIn(task, CELERY_BEAT_SCHEDULE)

    def test_all_test_tasks_disabled(self):
        """Test that all test tasks are disabled."""
        test_tasks = [
            name for name in CELERY_BEAT_SCHEDULE.keys() if name.startswith("test-")
        ]

        for task_name in test_tasks:
            config = CELERY_BEAT_SCHEDULE[task_name]
            self.assertFalse(
                config.get("enabled", True), f"Test task {task_name} should be disabled"
            )

    def test_all_tasks_importable(self):
        """Test that all task functions can be imported."""
        for task_name, config in CELERY_BEAT_SCHEDULE.items():
            with self.subTest(task=task_name):
                task_path = config["task"]
                module_path, function_name = task_path.rsplit(".", 1)

                try:
                    module = __import__(module_path, fromlist=[function_name])
                    task_function = getattr(module, function_name)

                    self.assertTrue(callable(task_function))
                    self.assertTrue(hasattr(task_function, "delay"))
                    self.assertTrue(hasattr(task_function, "apply_async"))

                except ImportError as e:
                    self.fail(f"Cannot import task '{task_path}': {e}")
                except AttributeError as e:
                    self.fail(
                        f"Task function '{function_name}' not found in module '{module_path}': {e}"
                    )

    def test_cron_configuration_summary(self):
        """Test cron configuration summary for completeness."""
        total_tasks = len(CELERY_BEAT_SCHEDULE)
        production_tasks = len(
            [
                name
                for name in CELERY_BEAT_SCHEDULE.keys()
                if not name.startswith("test-")
            ]
        )
        test_tasks = len(
            [name for name in CELERY_BEAT_SCHEDULE.keys() if name.startswith("test-")]
        )

        self.assertGreaterEqual(
            total_tasks, 15, "Should have at least 15 tasks configured"
        )
        self.assertGreaterEqual(
            production_tasks, 13, "Should have at least 13 production tasks"
        )
        self.assertGreaterEqual(test_tasks, 1, "Should have at least 1 test task")

        for task_name, config in CELERY_BEAT_SCHEDULE.items():
            if task_name.startswith("test-"):
                self.assertFalse(
                    config.get("enabled", True),
                    f"Test task {task_name} should be disabled",
                )
