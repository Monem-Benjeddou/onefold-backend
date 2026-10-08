import pytest
from django.core.cache import cache


@pytest.fixture(autouse=True)
def _fresh_cache():
    # Throttle counters and login lockouts live in the cache; keep tests independent.
    cache.clear()
    yield
    cache.clear()
