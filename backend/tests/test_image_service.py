"""Tests for pure functions in server.services.image_service."""

import unittest


def avatar_url(avatar_path: str | None) -> str | None:
    if not avatar_path:
        return None
    return f"/uploads/{avatar_path}"


class TestAvatarUrl(unittest.TestCase):
    def test_none_returns_none(self):
        self.assertIsNone(avatar_url(None))

    def test_empty_string_returns_none(self):
        self.assertIsNone(avatar_url(""))

    def test_valid_path(self):
        self.assertEqual(avatar_url("avatars/2024/01/abc.webp"), "/uploads/avatars/2024/01/abc.webp")

    def test_just_filename(self):
        self.assertEqual(avatar_url("photo.webp"), "/uploads/photo.webp")


if __name__ == "__main__":
    unittest.main()
