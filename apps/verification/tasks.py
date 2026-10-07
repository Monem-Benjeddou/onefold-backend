from celery import shared_task

from . import services


@shared_task(name="verification.run_check", acks_late=True)
def run_check_task(check_run_id):
    services.run_check(check_run_id)
