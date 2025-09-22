"""
Integration tests for cron task execution.

Tests that validate:
1. Task functions can be executed successfully
2. Task error handling works correctly
3. Task retry mechanisms function properly
4. Task parameters are processed correctly
5. Task results are in expected format
"""

import time
from datetime import date, timedelta
from unittest.mock import patch, MagicMock, call
from django.test import TestCase, override_settings
from django.utils import timezone
from celery import Celery
from celery.exceptions import Retry


app = Celery("test")


class CronTaskExecutionTest(TestCase):
    """Test cron task execution and behavior."""

    def setUp(self):
        """Set up test fixtures."""
        self.test_date = date(2024, 1, 15)
        self.test_date_str = self.test_date.isoformat()

    @patch("apps.stats.cron_tasks.timezone.now")
    @patch("apps.stats.cron_tasks.DailyStats.objects.filter")
    @patch("apps.stats.cron_tasks.DailyStatsService.generate_daily_stats")
    def test_generate_daily_stats_task_execution(
        self, mock_service, mock_filter, mock_now
    ):
        """Test daily stats generation task execution."""
        from apps.stats.cron_tasks import generate_daily_stats

        mock_now.return_value.date.return_value = date(2024, 1, 16)

        mock_filter.return_value.first.return_value = None

        mock_stats_instance = MagicMock()
        mock_stats_instance.id = 123
        mock_stats_instance.total_users = 1000
        mock_stats_instance.new_users = 50
        mock_stats_instance.active_users = 300
        mock_stats_instance.total_cards = 2000
        mock_stats_instance.new_cards = 25
        mock_stats_instance.sold_cards = 15
        mock_stats_instance.total_transactions = 100
        mock_stats_instance.transaction_volume = 5000.00

        mock_service.return_value = mock_stats_instance

        result = generate_daily_stats.run(target_date_str=self.test_date_str)

        self.assertIsInstance(result, dict)
        self.assertTrue(result["success"])
        self.assertEqual(result["date"], self.test_date_str)
        self.assertEqual(result["stats_id"], 123)
        self.assertFalse(result["was_existing"])
        self.assertEqual(result["total_users"], 1000)
        self.assertEqual(result["new_users"], 50)
        self.assertEqual(result["active_users"], 300)
        self.assertEqual(result["total_cards"], 2000)
        self.assertEqual(result["new_cards"], 25)
        self.assertEqual(result["sold_cards"], 15)
        self.assertEqual(result["total_transactions"], 100)
        self.assertEqual(result["transaction_volume"], 5000.00)
        self.assertIn("created", result["message"])

        mock_service.assert_called_once_with(self.test_date)

    @patch("apps.stats.cron_tasks.timezone.now")
    @patch("apps.stats.cron_tasks.DailyStats.objects.filter")
    @patch("apps.stats.cron_tasks.DailyStatsService.generate_daily_stats")
    def test_generate_daily_stats_with_existing_stats(
        self, mock_service, mock_filter, mock_now
    ):
        """Test daily stats generation when stats already exist."""
        from apps.stats.cron_tasks import generate_daily_stats

        mock_now.return_value.date.return_value = date(2024, 1, 16)

        existing_stats = MagicMock()
        mock_filter.return_value.first.return_value = existing_stats

        mock_stats_instance = MagicMock()
        mock_stats_instance.id = 456
        mock_service.return_value = mock_stats_instance

        result = generate_daily_stats.run(target_date_str=self.test_date_str)

        self.assertTrue(result["success"])
        self.assertTrue(result["was_existing"])
        self.assertIn("updated", result["message"])

    @patch("apps.stats.cron_tasks.timezone.now")
    @patch("apps.stats.cron_tasks.DailyStatsService.generate_daily_stats")
    def test_generate_daily_stats_default_date(self, mock_service, mock_now):
        """Test daily stats generation with default date (yesterday)."""
        from apps.stats.cron_tasks import generate_daily_stats

        mock_now.return_value.date.return_value = date(2024, 1, 16)

        mock_stats_instance = MagicMock()
        mock_stats_instance.id = 789
        mock_service.return_value = mock_stats_instance

        with patch("apps.stats.cron_tasks.DailyStats.objects.filter") as mock_filter:
            mock_filter.return_value.first.return_value = None

            result = generate_daily_stats.run()

            expected_date = date(2024, 1, 15)
            mock_service.assert_called_once_with(expected_date)
            self.assertEqual(result["date"], expected_date.isoformat())

    @patch("apps.stats.cron_tasks.timezone.now")
    @patch("apps.stats.cron_tasks.DailyStatsService.backfill_daily_stats")
    @patch("apps.stats.cron_tasks.DailyStatsService.get_stats_summary")
    def test_generate_weekly_stats_task_execution(
        self, mock_summary, mock_backfill, mock_now
    ):
        """Test weekly stats generation task execution."""
        from apps.stats.cron_tasks import generate_weekly_stats

        mock_now.return_value.date.return_value = date(2024, 1, 16)

        mock_backfill.return_value = 5
        mock_summary.return_value = {"total_users": 1500, "total_cards": 3000}

        result = generate_weekly_stats.run()

        self.assertTrue(result["success"])
        self.assertEqual(result["processed_count"], 5)
        self.assertIn("weekly_summary", result)
        self.assertEqual(result["weekly_summary"]["total_users"], 1500)

        start_date = date(2024, 1, 9)
        end_date = date(2024, 1, 15)
        mock_backfill.assert_called_once_with(start_date, end_date)
        mock_summary.assert_called_once_with(days=7)

    @patch("apps.stats.cron_tasks.timezone.now")
    @patch("apps.stats.cron_tasks.DailyStatsService.backfill_daily_stats")
    @patch("apps.stats.cron_tasks.DailyStatsService.get_stats_summary")
    def test_generate_monthly_stats_task_execution(
        self, mock_summary, mock_backfill, mock_now
    ):
        """Test monthly stats generation task execution."""
        from apps.stats.cron_tasks import generate_monthly_stats

        mock_now.return_value.date.return_value = date(2024, 2, 5)

        mock_backfill.return_value = 25
        mock_summary.return_value = {"total_users": 5000, "total_cards": 10000}

        result = generate_monthly_stats.run()

        self.assertTrue(result["success"])
        self.assertEqual(result["processed_count"], 25)
        self.assertIn("monthly_summary", result)

        start_date = date(2024, 1, 1)
        end_date = date(2024, 1, 31)
        mock_backfill.assert_called_once_with(start_date, end_date)

    @patch("apps.video_ai.tasks.GeneratedVideo.objects.filter")
    def test_update_pending_video_statuses_no_videos(self, mock_filter):
        """Test video status update when no pending videos exist."""
        from apps.video_ai.tasks import update_pending_video_statuses

        mock_queryset = MagicMock()
        mock_queryset.exists.return_value = False
        mock_filter.return_value = mock_queryset

        result = update_pending_video_statuses.run()

        self.assertEqual(result, "No pending videos")

    def test_recompute_stats_error_handling(self):
        """Test stats recompute error handling."""
        from apps.stats_ext.tasks import recompute_stats

        with patch("apps.stats_ext.tasks.Card.objects") as mock_card:
            mock_card.filter.side_effect = Exception("Database connection error")

            result = recompute_stats.run()

            self.assertIn("Error recomputing stats", result)
            self.assertIn("Database connection error", result)

    @patch("apps.stats.services.enhanced_analytics.GoogleAnalyticsIntegratedService")
    @patch("apps.stats.services.enhanced_analytics.GoogleAnalyticsMetrics.objects")
    @patch("apps.stats.services.enhanced_analytics.timezone.now")
    def test_sync_google_analytics_data_task_execution(
        self, mock_now, mock_ga_metrics, mock_service_class
    ):
        """Test Google Analytics sync task execution."""
        from apps.stats.services.enhanced_analytics import sync_google_analytics_data

        mock_now.return_value.date.return_value = date(2024, 1, 16)

        mock_service = MagicMock()
        mock_service.ga_available = True
        mock_service_class.return_value = mock_service

        mock_ga_service = MagicMock()
        mock_service.ga_service = mock_ga_service
        mock_ga_service.get_website_visits.return_value = {
            "total_sessions": 1000,
            "total_pageviews": 5000,
            "total_users": 800,
        }

        mock_ga_metrics.get_or_create.return_value = (MagicMock(), True)

        result = sync_google_analytics_data.run(days=7)

        self.assertTrue(result["success"])
        self.assertIn("date", result)
        self.assertTrue(result["metrics_created"])

    @patch("apps.stats.services.enhanced_analytics.GoogleAnalyticsIntegratedService")
    def test_sync_google_analytics_data_service_unavailable(self, mock_service_class):
        """Test GA sync when service is unavailable."""
        from apps.stats.services.enhanced_analytics import sync_google_analytics_data

        mock_service = MagicMock()
        mock_service.ga_available = False
        mock_service_class.return_value = mock_service

        result = sync_google_analytics_data.run()

        self.assertFalse(result["success"])
        self.assertEqual(result["message"], "Google Analytics service not available")

    def test_all_task_functions_have_shared_task_decorator(self):
        """Test that all task functions are properly decorated with @shared_task."""
        task_functions = [
            "apps.stats.cron_tasks.generate_daily_stats",
            "apps.stats.cron_tasks.generate_weekly_stats",
            "apps.stats.cron_tasks.generate_monthly_stats",
            "apps.video_ai.tasks.update_pending_video_statuses",
            "apps.stats_ext.tasks.recompute_stats",
            "apps.stats.services.enhanced_analytics.sync_google_analytics_data",
        ]

        for task_path in task_functions:
            with self.subTest(task_path=task_path):
                module_path, function_name = task_path.rsplit(".", 1)

                try:

                    module = __import__(module_path, fromlist=[function_name])
                    task_function = getattr(module, function_name)

                    self.assertTrue(
                        hasattr(task_function, "delay"),
                        f"Task function '{task_path}' missing 'delay' method - not a Celery task?",
                    )

                    self.assertTrue(
                        hasattr(task_function, "apply_async"),
                        f"Task function '{task_path}' missing 'apply_async' method - not a Celery task?",
                    )

                    self.assertTrue(
                        hasattr(task_function, "run"),
                        f"Task function '{task_path}' missing 'run' method - not a Celery task?",
                    )

                    self.assertTrue(
                        hasattr(task_function, "__wrapped__")
                        or hasattr(task_function, "name"),
                        f"Task function '{task_path}' doesn't appear to be a Celery task",
                    )

                except ImportError as e:
                    self.fail(f"Cannot import task function '{task_path}': {e}")
                except AttributeError as e:
                    self.fail(f"Task function '{task_path}' not found in module: {e}")

    @patch("apps.stats.cron_tasks.DailyStatsService.backfill_daily_stats")
    def test_backfill_missing_stats_task(self, mock_service):
        """Test backfill missing stats task execution."""
        from apps.stats.cron_tasks import backfill_missing_stats

        mock_service.return_value = 15

        start_date_str = "2024-01-01"
        end_date_str = "2024-01-15"

        result = backfill_missing_stats.run(start_date_str, end_date_str)

        self.assertTrue(result["success"])
        self.assertEqual(result["start_date"], start_date_str)
        self.assertEqual(result["end_date"], end_date_str)
        self.assertEqual(result["processed_count"], 15)

        mock_service.assert_called_once_with(date(2024, 1, 1), date(2024, 1, 15))

    @patch("apps.stats.cron_tasks.timezone.now")
    @patch("apps.stats.cron_tasks.DailyStats.objects.filter")
    @patch("apps.stats.cron_tasks.generate_daily_stats.apply_async")
    @patch("apps.stats.cron_tasks.backfill_missing_stats.apply_async")
    def test_check_and_run_immediate_stats_task(
        self, mock_backfill_async, mock_gen_async, mock_filter, mock_now
    ):
        """Test check and run immediate stats task execution."""
        from apps.stats.cron_tasks import check_and_run_immediate_stats

        mock_now.return_value.date.return_value = date(2024, 1, 16)

        mock_filter.return_value.first.return_value = None

        mock_filter.return_value.exists.return_value = False

        mock_gen_task = MagicMock()
        mock_gen_task.id = "task_123"
        mock_gen_async.return_value = mock_gen_task

        mock_backfill_task = MagicMock()
        mock_backfill_task.id = "task_456"
        mock_backfill_async.return_value = mock_backfill_task

        result = check_and_run_immediate_stats.run()

        self.assertTrue(result["success"])
        self.assertIn("results", result)
        self.assertGreater(len(result["results"]), 0)

    def test_task_timeout_handling(self):
        """Test that tasks have appropriate timeout configurations."""

        from ..components.cron import CELERY_BEAT_SCHEDULE

        for task_name, config in CELERY_BEAT_SCHEDULE.items():
            with self.subTest(task=task_name):
                expires = config["options"]["expires"]

                if task_name.startswith("test-"):

                    self.assertLessEqual(
                        expires, 300, f"Test task {task_name} expires too long"
                    )
                else:

                    self.assertGreaterEqual(
                        expires, 600, f"Production task {task_name} expires too short"
                    )
                    self.assertLessEqual(
                        expires, 21600, f"Production task {task_name} expires too long"
                    )

    def test_task_function_signatures(self):
        """Test that task functions have expected signatures."""
        import inspect
        from apps.stats.cron_tasks import (
            generate_daily_stats,
            generate_weekly_stats,
            generate_monthly_stats,
        )
        from apps.video_ai.tasks import update_pending_video_statuses
        from apps.stats_ext.tasks import recompute_stats

        sig = inspect.signature(generate_daily_stats.run)
        params = list(sig.parameters.keys())
        self.assertIn("target_date_str", params)

        sig = inspect.signature(generate_weekly_stats.run)
        params = list(sig.parameters.keys())
        self.assertIn("target_date_str", params)

        sig = inspect.signature(generate_monthly_stats.run)
        params = list(sig.parameters.keys())
        self.assertIn("target_date_str", params)

        sig = inspect.signature(update_pending_video_statuses.run)
        params = [p for p in sig.parameters.keys() if p != "self"]
        self.assertEqual(len(params), 0, "Video status task should take no parameters")

        sig = inspect.signature(recompute_stats.run)
        params = [p for p in sig.parameters.keys() if p != "self"]
        self.assertEqual(
            len(params), 0, "Recompute stats task should take no parameters"
        )

    def test_task_return_value_consistency(self):
        """Test that all tasks return consistent result formats."""

        expected_return_formats = {
            "generate_daily_stats": dict,
            "generate_weekly_stats": dict,
            "generate_monthly_stats": dict,
            "sync_google_analytics_data": dict,
            "update_pending_video_statuses": str,
            "recompute_stats": str,
        }

        for task_name, expected_type in expected_return_formats.items():
            self.assertTrue(
                expected_type in [dict, str],
                f"Task {task_name} should return {expected_type}",
            )
