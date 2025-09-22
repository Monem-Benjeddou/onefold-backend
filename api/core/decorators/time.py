from time import time
import logging
from datetime import timedelta

logger = logging.getLogger(__name__)


def time_calculator(func):
    def wrapper(*args, **kwargs):
        time1 = time()
        func(*args, **kwargs)
        time2 = time()
        logger.info("Run Time : ", timedelta(time2 - time1).total_seconds())

    return wrapper
