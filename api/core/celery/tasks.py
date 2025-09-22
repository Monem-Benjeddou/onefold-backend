from celery import shared_task


@shared_task
def debug_task(message: str) -> str:
    return f"Debug: {message}"


