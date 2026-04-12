import time
import unittest

import jwt as pyjwt

from backend.services.jwt_auth import hash_password, verify_password

_TEST_SECRET = "test-secret-for-unit-tests"


class TestJwtCreateVerify(unittest.TestCase):
    """Test JWT create/verify using pyjwt directly (avoids Settings dependency)."""

    def _create(self, user_id: int) -> str:
        payload = {
            "sub": str(user_id),
            "iat": int(time.time()),
            "exp": int(time.time()) + 3600,
        }
        return pyjwt.encode(payload, _TEST_SECRET, algorithm="HS256")

    def _verify(self, token: str) -> dict | None:
        try:
            return pyjwt.decode(token, _TEST_SECRET, algorithms=["HS256"])
        except (pyjwt.ExpiredSignatureError, pyjwt.InvalidTokenError):
            return None

    def test_roundtrip(self):
        token = self._create(42)
        payload = self._verify(token)
        self.assertIsNotNone(payload)
        self.assertEqual(payload["sub"], "42")

    def test_invalid_token(self):
        self.assertIsNone(self._verify("invalid-token"))

    def test_empty_token(self):
        self.assertIsNone(self._verify(""))

    def test_payload_has_exp_iat(self):
        token = self._create(1)
        payload = self._verify(token)
        self.assertIn("iat", payload)
        self.assertIn("exp", payload)
        self.assertGreater(payload["exp"], payload["iat"])

    def test_wrong_secret_fails(self):
        token = self._create(1)
        result = None
        try:
            result = pyjwt.decode(token, "wrong-secret", algorithms=["HS256"])
        except pyjwt.InvalidTokenError:
            result = None
        self.assertIsNone(result)

    def test_expired_token(self):
        payload = {
            "sub": "1",
            "iat": int(time.time()) - 7200,
            "exp": int(time.time()) - 3600,
        }
        token = pyjwt.encode(payload, _TEST_SECRET, algorithm="HS256")
        self.assertIsNone(self._verify(token))


class TestPasswordHashing(unittest.TestCase):
    def test_roundtrip(self):
        pw = "my_secret_password"
        hashed = hash_password(pw)
        self.assertTrue(verify_password(pw, hashed))

    def test_wrong_password(self):
        hashed = hash_password("correct")
        self.assertFalse(verify_password("wrong", hashed))

    def test_different_hashes(self):
        h1 = hash_password("same")
        h2 = hash_password("same")
        self.assertNotEqual(h1, h2)
        self.assertTrue(verify_password("same", h1))
        self.assertTrue(verify_password("same", h2))

    def test_invalid_hash_returns_false(self):
        self.assertFalse(verify_password("pw", "not-a-hash"))


if __name__ == "__main__":
    unittest.main()
