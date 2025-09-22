"""
Test cron task for creating timestamped files.
"""

import os
from datetime import datetime
from celery import shared_task
from django.conf import settings


@shared_task(bind=True)
def create_test_file(self):
    """
    Creates a timestamped file in the test-cron folder every 5 minutes.
    This is used to verify that the cron job system is working correctly.
    """
    try:

        test_cron_dir = os.path.join(settings.BASE_DIR, "test-cron")
        os.makedirs(test_cron_dir, exist_ok=True)

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"test_cron_{timestamp}.txt"
        filepath = os.path.join(test_cron_dir, filename)

        content = f"""Test Cron Job Execution
Task ID: {self.request.id}
Timestamp: {datetime.now().isoformat()}
Created by: core.tasks.test_cron.create_test_file
Status: SUCCESS
"""

        with open(filepath, "w") as f:
            f.write(content)

        print(f"Test cron file created: {filepath}")
        return f"Successfully created test file: {filename}"

    except Exception as e:
        print(f"Error creating test cron file: {str(e)}")
        raise e
