"""
Integration tests for cron task basic functionality.

Tests that validate:
1. Task functions can be imported successfully
2. Task decorators are properly applied
3. Task signatures are correct
4. Task metadata is available
5. Basic task execution patterns work
"""

import inspect
from unittest.mock import patch, MagicMock
from django.test import TestCase
from django.utils import timezone
from datetime import date, timedelta


class CronTaskIntegrationTest(TestCase):
    """Test cron task integration and basic functionality."""

    def test_all_cron_tasks_can_be_imported(self):
        """Test that all cron tasks can be imported without errors."""
        from ..components.cron import CELERY_BEAT_SCHEDULE

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
                    self.assertTrue(hasattr(task_function, "run"))

                except ImportError as e:
                    self.fail(f"Cannot import task '{task_path}': {e}")
                except AttributeError as e:
                    self.fail(
                        f"Task function '{function_name}' not found in module '{module_path}': {e}"
                    )

    def test_stats_tasks_have_proper_signatures(self):
        """Test that stats tasks have the expected function signatures."""
        from apps.stats.cron_tasks import (
            generate_daily_stats,
            generate_weekly_stats,
            generate_monthly_stats,
            backfill_missing_stats,
        )

        sig = inspect.signature(generate_daily_stats.run)
        params = list(sig.parameters.keys())
        self.assertIn("target_date_str", params)

        sig = inspect.signature(generate_weekly_stats.run)
        params = list(sig.parameters.keys())
        self.assertIn("target_date_str", params)

        sig = inspect.signature(generate_monthly_stats.run)
        params = list(sig.parameters.keys())
        self.assertIn("target_date_str", params)

        sig = inspect.signature(backfill_missing_stats.run)
        params = list(sig.parameters.keys())
        self.assertIn("start_date_str", params)
        self.assertIn("end_date_str", params)

    def test_video_ai_tasks_have_proper_signatures(self):
        """Test that video AI tasks have the expected function signatures."""
        from apps.video_ai.tasks import update_pending_video_statuses

        sig = inspect.signature(update_pending_video_statuses.run)
        params = [p for p in sig.parameters.keys() if p != "self"]
        self.assertEqual(len(params), 0, "Video task should not require parameters")

    def test_stats_ext_tasks_have_proper_signatures(self):
        """Test that stats extension tasks have the expected function signatures."""
        from apps.stats_ext.tasks import recompute_stats

        sig = inspect.signature(recompute_stats.run)
        params = [p for p in sig.parameters.keys() if p != "self"]
        self.assertEqual(len(params), 0, "Stats ext task should not require parameters")

    def test_ga_sync_task_has_proper_signature(self):
        """Test that GA sync task has the expected function signature."""
        from apps.stats.services.enhanced_analytics import sync_google_analytics_data

        sig = inspect.signature(sync_google_analytics_data.run)
        params = list(sig.parameters.keys())
        self.assertIn("days", params)

    def test_task_names_match_configuration(self):
        """Test that task names in configuration match actual task names."""
        from ..components.cron import CELERY_BEAT_SCHEDULE

        expected_mappings = {
            "daily-stats-generation": "apps.stats.cron_tasks.generate_daily_stats",
            "weekly-stats-generation": "apps.stats.cron_tasks.generate_weekly_stats",
            "monthly-stats-generation": "apps.stats.cron_tasks.generate_monthly_stats",
            "google-analytics-sync-daily": "apps.stats.services.enhanced_analytics.sync_google_analytics_data",
            "google-analytics-sync-weekly": "apps.stats.services.enhanced_analytics.sync_google_analytics_data",
            "update-pending-video-statuses": "apps.video_ai.tasks.update_pending_video_statuses",
            "stats-ext-nightly-recompute": "apps.stats_ext.tasks.recompute_stats",
        }

        for schedule_name, expected_task_path in expected_mappings.items():
            with self.subTest(schedule=schedule_name):
                self.assertIn(schedule_name, CELERY_BEAT_SCHEDULE)
                actual_task_path = CELERY_BEAT_SCHEDULE[schedule_name]["task"]
                self.assertEqual(actual_task_path, expected_task_path)

    def test_task_configuration_completeness(self):
        """Test that all tasks have complete configuration."""
        from ..components.cron import CELERY_BEAT_SCHEDULE

        required_fields = ["task", "schedule", "options"]
        required_options = ["expires"]

        for task_name, config in CELERY_BEAT_SCHEDULE.items():
            with self.subTest(task=task_name):

                for field in required_fields:
                    self.assertIn(
                        field, config, f"Task '{task_name}' missing field '{field}'"
                    )

                for option in required_options:
                    self.assertIn(
                        option,
                        config["options"],
                        f"Task '{task_name}' missing option '{option}'",
                    )

                expires = config["options"]["expires"]
                self.assertIsInstance(expires, int)
                self.assertGreater(expires, 0)

    def test_task_docstrings_exist(self):
        """Test that all task functions have proper docstrings."""
        from ..components.cron import CELERY_BEAT_SCHEDULE

        for task_name, config in CELERY_BEAT_SCHEDULE.items():
            with self.subTest(task=task_name):
                task_path = config["task"]
                module_path, function_name = task_path.rsplit(".", 1)

                try:
                    module = __import__(module_path, fromlist=[function_name])
                    task_function = getattr(module, function_name)

                    self.assertIsNotNone(
                        task_function.__doc__,
                        f"Task function '{task_path}' should have a docstring",
                    )
                    self.assertGreater(
                        len(task_function.__doc__.strip()),
                        10,
                        f"Task function '{task_path}' should have a meaningful docstring",
                    )

                except ImportError:
                    self.skipTest(
                        f"Cannot import task '{task_path}' for docstring check"
                    )

    def test_celery_task_decorators(self):
        """Test that tasks have proper Celery decorators applied."""
        task_functions = [
            ("apps.stats.cron_tasks", "generate_daily_stats"),
            ("apps.stats.cron_tasks", "generate_weekly_stats"),
            ("apps.stats.cron_tasks", "generate_monthly_stats"),
            ("apps.stats.cron_tasks", "backfill_missing_stats"),
            ("apps.video_ai.tasks", "update_pending_video_statuses"),
            ("apps.stats_ext.tasks", "recompute_stats"),
            ("apps.stats.services.enhanced_analytics", "sync_google_analytics_data"),
        ]

        for module_path, function_name in task_functions:
            with self.subTest(task=f"{module_path}.{function_name}"):
                try:
                    module = __import__(module_path, fromlist=[function_name])
                    task_function = getattr(module, function_name)

                    self.assertTrue(
                        hasattr(task_function, "_decorated"),
                        f"Task '{function_name}' should be decorated with @shared_task",
                    )

                    self.assertTrue(
                        hasattr(task_function, "name")
                        or hasattr(task_function, "__wrapped__"),
                        f"Task '{function_name}' should have Celery task metadata",
                    )

                except ImportError:
                    self.skipTest(f"Cannot import task '{module_path}.{function_name}'")

    def test_task_retry_configurations(self):
        """Test that tasks with retry have proper retry configurations."""

        retry_tasks = [
            "apps.stats.cron_tasks.generate_daily_stats",
            "apps.stats.cron_tasks.generate_weekly_stats",
            "apps.stats.cron_tasks.generate_monthly_stats",
            "apps.stats.cron_tasks.backfill_missing_stats",
            "apps.stats.services.enhanced_analytics.sync_google_analytics_data",
        ]

        for task_path in retry_tasks:
            with self.subTest(task=task_path):
                module_path, function_name = task_path.rsplit(".", 1)

                try:
                    module = __import__(module_path, fromlist=[function_name])
                    task_function = getattr(module, function_name)

                    self.assertTrue(
                        hasattr(task_function, "max_retries")
                        or hasattr(task_function, "retry")
                        or "bind=True" in str(task_function),
                        f"Task '{task_path}' should be configured for retries",
                    )

                except ImportError:
                    self.skipTest(f"Cannot import task '{task_path}'")

    def test_test_tasks_are_disabled_in_production(self):
        """Test that test tasks are properly disabled."""
        from ..components.cron import CELERY_BEAT_SCHEDULE

        test_task_names = [
            name for name in CELERY_BEAT_SCHEDULE.keys() if name.startswith("test-")
        ]

        for task_name in test_task_names:
            with self.subTest(task=task_name):
                config = CELERY_BEAT_SCHEDULE[task_name]

                self.assertIn("enabled", config)
                self.assertFalse(
                    config["enabled"], f"Test task '{task_name}' should be disabled"
                )

                schedule = config["schedule"]
                if isinstance(schedule, (int, float)):
                    self.assertLessEqual(
                        schedule,
                        60,
                        f"Test task '{task_name}' should have short interval",
                    )

    def test_production_tasks_scheduling_no_conflicts(self):
        """Test that production tasks don't have scheduling conflicts."""
        from ..components.cron import CELERY_BEAT_SCHEDULE
        from celery.schedules import crontab

        production_tasks = {
            name: config
            for name, config in CELERY_BEAT_SCHEDULE.items()
            if not name.startswith("test-") and config.get("enabled", True)
        }

        crontab_schedules = {}

        for task_name, config in production_tasks.items():
            schedule = config["schedule"]

            if isinstance(schedule, crontab):

                key = (
                    tuple(schedule.hour) if schedule.hour else (0,),
                    tuple(schedule.minute) if schedule.minute else (0,),
                    tuple(schedule.day_of_week) if schedule.day_of_week else None,
                    tuple(schedule.day_of_month) if schedule.day_of_month else None,
                )

                if key not in crontab_schedules:
                    crontab_schedules[key] = []
                crontab_schedules[key].append(task_name)

        for schedule_key, tasks in crontab_schedules.items():
            if len(tasks) > 1:

                hour, minute, dow, dom = schedule_key

                if dow is None and dom is None:

                    if len(set(minute)) == 1:
                        self.fail(
                            f"Scheduling conflict: Tasks {tasks} all run at the same time {hour}:{minute}"
                        )

    def test_task_parameter_defaults(self):
        """Test that tasks handle default parameters correctly."""
        from apps.stats.cron_tasks import generate_daily_stats

        sig = inspect.signature(generate_daily_stats.run)

        if "target_date_str" in sig.parameters:
            param = sig.parameters["target_date_str"]
            self.assertEqual(param.default, None)

    def test_google_analytics_tasks_have_kwargs(self):
        """Test that Google Analytics tasks have proper kwargs configuration."""
        from ..components.cron import CELERY_BEAT_SCHEDULE

        ga_tasks = [
            "google-analytics-sync-daily",
            "google-analytics-sync-weekly",
        ]

        for task_name in ga_tasks:
            with self.subTest(task=task_name):
                config = CELERY_BEAT_SCHEDULE[task_name]

                self.assertIn(
                    "kwargs", config, f"GA task '{task_name}' should have kwargs"
                )

                self.assertIn(
                    "days",
                    config["kwargs"],
                    f"GA task '{task_name}' should have 'days' in kwargs",
                )

                days = config["kwargs"]["days"]
                self.assertIsInstance(days, int)
                self.assertGreater(days, 0)

    def test_task_schedule_types_are_valid(self):
        """Test that all task schedules use valid types."""
        from ..components.cron import CELERY_BEAT_SCHEDULE
        from celery.schedules import crontab

        valid_schedule_types = (crontab, int, float)

        for task_name, config in CELERY_BEAT_SCHEDULE.items():
            with self.subTest(task=task_name):
                schedule = config["schedule"]

                self.assertIsInstance(
                    schedule,
                    valid_schedule_types,
                    f"Task '{task_name}' has invalid schedule type: {type(schedule)}",
                )

                if isinstance(schedule, (int, float)):
                    self.assertGreater(
                        schedule,
                        0,
                        f"Task '{task_name}' has non-positive schedule interval: {schedule}",
                    )

    def test_celery_beat_scheduler_configuration(self):
        """Test that Celery beat scheduler is properly configured."""
        from ..components.cron import (
            CELERY_BEAT_SCHEDULER,
            CELERY_BEAT_SCHEDULE_FILENAME,
        )

        self.assertEqual(
            CELERY_BEAT_SCHEDULER,
            "core.schedulers.patched_database_scheduler:PatchedDatabaseScheduler",
        )

        self.assertEqual(CELERY_BEAT_SCHEDULE_FILENAME, "celerybeat-schedule")

    def test_task_module_structure(self):
        """Test that task modules are properly structured."""
        task_modules = [
            "apps.stats.cron_tasks",
            "apps.video_ai.tasks",
            "apps.stats_ext.tasks",
            "apps.stats.services.enhanced_analytics",
        ]

        for module_path in task_modules:
            with self.subTest(module=module_path):
                try:
                    module = __import__(module_path, fromlist=[""])

                    self.assertIsNotNone(module)

                    has_shared_task = False
                    for attr_name in dir(module):
                        attr = getattr(module, attr_name)
                        if (
                            hasattr(attr, "delay")
                            and hasattr(attr, "apply_async")
                            and hasattr(attr, "run")
                            and callable(attr)
                        ):
                            has_shared_task = True
                            break

                    self.assertTrue(
                        has_shared_task,
                        f"Module '{module_path}' should contain at least one Celery task",
                    )

                except ImportError as e:
                    self.fail(f"Cannot import task module '{module_path}': {e}")

    def test_configuration_constants_are_defined(self):
        """Test that all required configuration constants are defined."""
        from config.settings.components import cron

        required_constants = [
            "CELERY_BEAT_SCHEDULE",
            "CELERY_BEAT_SCHEDULER",
            "CELERY_BEAT_SCHEDULE_FILENAME",
        ]

        for constant in required_constants:
            with self.subTest(constant=constant):
                self.assertTrue(
                    hasattr(cron, constant),
                    f"Cron configuration should define '{constant}'",
                )
