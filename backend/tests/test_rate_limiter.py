import unittest

from backend.services.api_middlewares import SlidingWindowRateLimiter


class TestSlidingWindowRateLimiter(unittest.TestCase):
    def test_allows_under_limit(self):
        rl = SlidingWindowRateLimiter()
        allowed, retry_after = rl.allow("key1", limit=3, window_s=60)
        self.assertTrue(allowed)
        self.assertIsNone(retry_after)

    def test_blocks_at_limit(self):
        rl = SlidingWindowRateLimiter()
        for _ in range(5):
            rl.allow("key2", limit=5, window_s=60)
        allowed, retry_after = rl.allow("key2", limit=5, window_s=60)
        self.assertFalse(allowed)
        self.assertIsNotNone(retry_after)
        self.assertGreater(retry_after, 0)

    def test_different_keys_independent(self):
        rl = SlidingWindowRateLimiter()
        for _ in range(5):
            rl.allow("key_a", limit=5, window_s=60)
        allowed_a, _ = rl.allow("key_a", limit=5, window_s=60)
        allowed_b, _ = rl.allow("key_b", limit=5, window_s=60)
        self.assertFalse(allowed_a)
        self.assertTrue(allowed_b)

    def test_retry_after_is_positive(self):
        rl = SlidingWindowRateLimiter()
        for _ in range(3):
            rl.allow("k", limit=3, window_s=10)
        _, retry_after = rl.allow("k", limit=3, window_s=10)
        self.assertGreater(retry_after, 0)
        self.assertLessEqual(retry_after, 10)


if __name__ == "__main__":
    unittest.main()
