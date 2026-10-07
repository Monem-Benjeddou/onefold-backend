"""The beat schedule must only reference code that exists, or beat fails at runtime."""

import importlib.util

import pytest
from django.utils.module_loading import import_string

from api.config.settings.components.cron import CELERY_BEAT_SCHEDULE, CELERY_BEAT_SCHEDULER


@pytest.mark.parametrize("name", sorted(CELERY_BEAT_SCHEDULE))
def test_scheduled_task_is_importable(name):
    task = import_string(CELERY_BEAT_SCHEDULE[name]["task"])
    assert hasattr(task, "delay"), f"{name} is not a Celery task"


def test_scheduler_module_exists():
    # Importing the scheduler loads django_celery_beat models, which the test
    # settings don't install; checking the module is enough to catch a bad path.
    module, _, attr = CELERY_BEAT_SCHEDULER.partition(":")
    assert attr
    assert importlib.util.find_spec(module) is not None
