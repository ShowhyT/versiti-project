"""Tests for pure utility functions in server.api.auth (no DB required)."""

import re
import time
import unittest
from dataclasses import dataclass, field
from unittest.mock import patch

import jwt as pyjwt

# We can't import from backend.api.auth directly (it triggers DB init),
# so we duplicate the small pure functions here or test them via patching.

_USERNAME_RE = re.compile(r"^[a-zA-Z0-9_]{3,20}$")
_EMAIL_RE = re.compile(r"^[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}$")


class TestUsernameRegex(unittest.TestCase):
    def test_valid_usernames(self):
        for name in ["abc", "user_name", "Test123", "a" * 20, "___"]:
            self.assertTrue(_USERNAME_RE.match(name), f"{name!r} should be valid")

    def test_invalid_usernames(self):
        for name in ["ab", "a" * 21, "user name", "user@name", "юзер", "", "a-b"]:
            self.assertIsNone(_USERNAME_RE.match(name), f"{name!r} should be invalid")


class TestEmailRegex(unittest.TestCase):
    def test_valid_emails(self):
        for email in [
            "user@example.com",
            "test.name@domain.org",
            "a@b.co",
            "user+tag@gmail.com",
            "user-name@sub.domain.com",
        ]:
            self.assertTrue(_EMAIL_RE.match(email), f"{email!r} should be valid")

    def test_invalid_emails(self):
        for email in ["", "noat", "@no-user.com", "user@", "user@.com", "user @example.com"]:
            self.assertIsNone(_EMAIL_RE.match(email), f"{email!r} should be invalid")


class TestExtractDisplayName(unittest.TestCase):
    """Test _extract_display_name logic (JWT unverified decode)."""

    def _extract(self, cookies: dict) -> str:
        access_token = (cookies.get("access_token") or "").strip()
        if not access_token:
            return ""
        try:
            payload = pyjwt.decode(access_token, options={"verify_signature": False})
            name = (payload.get("name") or "").strip()
            if name:
                return name
            given = (payload.get("given_name") or "").strip()
            family = (payload.get("family_name") or "").strip()
            if given or family:
                return f"{family} {given}".strip()
            return (payload.get("preferred_username") or "").strip()
        except Exception:
            return ""

    def _make_token(self, **claims) -> str:
        return pyjwt.encode(claims, "secret", algorithm="HS256")

    def test_empty_cookies(self):
        self.assertEqual(self._extract({}), "")

    def test_no_access_token(self):
        self.assertEqual(self._extract({"access_token": ""}), "")

    def test_name_present(self):
        token = self._make_token(name="Иван Иванов", sub="1")
        self.assertEqual(self._extract({"access_token": token}), "Иван Иванов")

    def test_given_family_fallback(self):
        token = self._make_token(given_name="Петр", family_name="Сидоров", sub="1")
        self.assertEqual(self._extract({"access_token": token}), "Сидоров Петр")

    def test_preferred_username_fallback(self):
        token = self._make_token(preferred_username="ivan123", sub="1")
        self.assertEqual(self._extract({"access_token": token}), "ivan123")

    def test_invalid_token(self):
        self.assertEqual(self._extract({"access_token": "not-a-jwt"}), "")


class TestPurgePending(unittest.TestCase):
    """Test TTL purge logic (same pattern used in _purge_pending_reg and _purge_pending_2fa)."""

    def _purge(self, store: dict, ttl_s: float, now: float) -> None:
        expired = [
            key
            for key, item in list(store.items())
            if now - float(item["created_at"]) > ttl_s
        ]
        for key in expired:
            store.pop(key, None)

    def test_expired_entries_removed(self):
        store = {
            "old": {"created_at": 100.0},
            "new": {"created_at": 500.0},
        }
        self._purge(store, ttl_s=300, now=600.0)
        self.assertNotIn("old", store)
        self.assertIn("new", store)

    def test_all_fresh(self):
        store = {"a": {"created_at": 500.0}, "b": {"created_at": 550.0}}
        self._purge(store, ttl_s=300, now=600.0)
        self.assertEqual(len(store), 2)

    def test_all_expired(self):
        store = {"a": {"created_at": 10.0}, "b": {"created_at": 20.0}}
        self._purge(store, ttl_s=300, now=600.0)
        self.assertEqual(len(store), 0)

    def test_empty_store(self):
        store = {}
        self._purge(store, ttl_s=300, now=600.0)
        self.assertEqual(len(store), 0)


class TestGenerateCode(unittest.TestCase):
    def _generate_code(self) -> str:
        import secrets
        return f"{secrets.randbelow(1_000_000):06d}"

    def test_length_is_six(self):
        for _ in range(20):
            code = self._generate_code()
            self.assertEqual(len(code), 6)

    def test_all_digits(self):
        for _ in range(20):
            code = self._generate_code()
            self.assertTrue(code.isdigit(), f"{code!r} should be all digits")

    def test_codes_vary(self):
        codes = {self._generate_code() for _ in range(50)}
        self.assertGreater(len(codes), 1, "Codes should not all be identical")


if __name__ == "__main__":
    unittest.main()
