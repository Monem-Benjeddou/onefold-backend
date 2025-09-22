from django.test import TestCase, RequestFactory, override_settings
from django.http import HttpResponse
from rest_framework import status
from django.core.cache import cache
from django.core.cache.backends.locmem import LocMemCache
from core.ratelimiter import dynamic_rate_limit


test_cache = LocMemCache("test_cache_name", {})


@dynamic_rate_limit(default_rate=3, default_period=60)
def test_view(request):
    return HttpResponse("OK")


class RateLimiterTests(TestCase):
    def setUp(self):
        self.factory = RequestFactory()

        cache.clear()

        import core.ratelimiter

        if hasattr(core.ratelimiter, "_test_rate_limit_cache"):
            core.ratelimiter._test_rate_limit_cache = {}

    def tearDown(self):

        cache.clear()

        import core.ratelimiter

        if hasattr(core.ratelimiter, "_test_rate_limit_cache"):
            core.ratelimiter._test_rate_limit_cache = {}

    @override_settings(
        RATE_LIMITER_ENABLED=True, _RATE_LIMIT_FORCE_ENABLED=True, TESTING=True
    )
    def test_rate_limiting_when_enabled(self):
        """Test that rate limiting is applied when enabled"""
        request = self.factory.get("/test/")

        for _ in range(3):
            response = test_view(request)
            self.assertEqual(response.status_code, 200)

        response = test_view(request)
        self.assertEqual(response.status_code, status.HTTP_429_TOO_MANY_REQUESTS)

    @override_settings(RATE_LIMITER_ENABLED=False)
    def test_rate_limiting_when_disabled(self):
        """Test that rate limiting is not applied when disabled"""
        request = self.factory.get("/test/")

        for _ in range(10):
            response = test_view(request)
            self.assertEqual(response.status_code, 200)

    @override_settings(TESTING=True, RATE_LIMITER_ENABLED=True)
    def test_rate_limiting_disabled_in_tests_by_default(self):
        """Test that rate limiting is disabled in tests by default"""
        request = self.factory.get("/test/")

        for _ in range(10):
            response = test_view(request)
            self.assertEqual(response.status_code, 200)

    @override_settings(
        TESTING=True, RATE_LIMITER_ENABLED=True, _RATE_LIMIT_FORCE_ENABLED=True
    )
    def test_rate_limiting_can_be_forced_in_tests(self):
        """Test that rate limiting can be enabled in tests with _RATE_LIMIT_FORCE_ENABLED"""
        request = self.factory.get("/test/")

        for _ in range(3):
            response = test_view(request)
            self.assertEqual(response.status_code, 200)

        response = test_view(request)
        self.assertEqual(response.status_code, status.HTTP_429_TOO_MANY_REQUESTS)
