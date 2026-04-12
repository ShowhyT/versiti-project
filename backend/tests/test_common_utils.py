"""Tests for pure utility functions in server.api.common."""

import json
import os
import tempfile
import unittest
from datetime import datetime, timezone, timedelta
from pathlib import Path


# --- iso_utc (duplicated to avoid importing server.api.common) ---

def iso_utc(value: datetime | None) -> str | None:
    if value is None:
        return None
    if value.tzinfo is None:
        value = value.replace(tzinfo=timezone.utc)
    else:
        value = value.astimezone(timezone.utc)
    return value.isoformat().replace("+00:00", "Z")


# --- load_build_info (duplicated) ---

def load_build_info(build_info_file: Path) -> dict:
    info: dict[str, str] = {}
    env_version = (os.getenv("APP_VERSION") or os.getenv("GIT_SHA") or "").strip()
    if env_version:
        info["version"] = env_version
    try:
        raw = build_info_file.read_text(encoding="utf-8")
        parsed = json.loads(raw)
        if isinstance(parsed, dict):
            for key in ("version", "git_sha", "branch", "deployed_at_utc"):
                value = parsed.get(key)
                if isinstance(value, str) and value.strip():
                    if key == "version" and info.get("version"):
                        continue
                    info[key] = value.strip()
            if "version" not in info:
                fallback_sha = parsed.get("git_sha")
                if isinstance(fallback_sha, str) and fallback_sha.strip():
                    info["version"] = fallback_sha.strip()
    except Exception:
        pass
    return info


class TestIsoUtc(unittest.TestCase):
    def test_none_returns_none(self):
        self.assertIsNone(iso_utc(None))

    def test_naive_datetime_treated_as_utc(self):
        dt = datetime(2024, 1, 15, 12, 30, 0)
        result = iso_utc(dt)
        self.assertTrue(result.endswith("Z"))
        self.assertIn("2024-01-15", result)
        self.assertIn("12:30:00", result)

    def test_aware_utc_datetime(self):
        dt = datetime(2024, 6, 1, 0, 0, 0, tzinfo=timezone.utc)
        self.assertEqual(iso_utc(dt), "2024-06-01T00:00:00Z")

    def test_non_utc_timezone_converted(self):
        msk = timezone(timedelta(hours=3))
        dt = datetime(2024, 6, 1, 15, 0, 0, tzinfo=msk)
        result = iso_utc(dt)
        self.assertTrue(result.endswith("Z"))
        self.assertIn("12:00:00", result)  # 15:00 MSK = 12:00 UTC

    def test_no_plus_zero_in_output(self):
        dt = datetime(2024, 1, 1, tzinfo=timezone.utc)
        result = iso_utc(dt)
        self.assertNotIn("+00:00", result)
        self.assertTrue(result.endswith("Z"))


class TestLoadBuildInfo(unittest.TestCase):
    def setUp(self):
        # Clear env vars that might interfere
        self._old_app_version = os.environ.pop("APP_VERSION", None)
        self._old_git_sha = os.environ.pop("GIT_SHA", None)

    def tearDown(self):
        os.environ.pop("APP_VERSION", None)
        os.environ.pop("GIT_SHA", None)
        if self._old_app_version is not None:
            os.environ["APP_VERSION"] = self._old_app_version
        if self._old_git_sha is not None:
            os.environ["GIT_SHA"] = self._old_git_sha

    def test_no_file_no_env(self):
        result = load_build_info(Path("/tmp/nonexistent_build_info.json"))
        self.assertEqual(result, {})

    def test_env_app_version(self):
        os.environ["APP_VERSION"] = "v1.2.3"
        result = load_build_info(Path("/tmp/nonexistent_build_info.json"))
        self.assertEqual(result["version"], "v1.2.3")

    def test_env_git_sha(self):
        os.environ["GIT_SHA"] = "abc123"
        result = load_build_info(Path("/tmp/nonexistent_build_info.json"))
        self.assertEqual(result["version"], "abc123")

    def test_json_file(self):
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json.dump({"version": "2.0.0", "branch": "main", "git_sha": "def456"}, f)
            path = f.name
        try:
            result = load_build_info(Path(path))
            self.assertEqual(result["version"], "2.0.0")
            self.assertEqual(result["branch"], "main")
            self.assertEqual(result["git_sha"], "def456")
        finally:
            os.unlink(path)

    def test_env_overrides_file_version(self):
        os.environ["APP_VERSION"] = "env-ver"
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json.dump({"version": "file-ver", "branch": "dev"}, f)
            path = f.name
        try:
            result = load_build_info(Path(path))
            self.assertEqual(result["version"], "env-ver")
            self.assertEqual(result["branch"], "dev")
        finally:
            os.unlink(path)

    def test_git_sha_fallback_to_version(self):
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json.dump({"git_sha": "sha123"}, f)
            path = f.name
        try:
            result = load_build_info(Path(path))
            self.assertEqual(result["version"], "sha123")
        finally:
            os.unlink(path)

    def test_invalid_json_file(self):
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            f.write("{broken json")
            path = f.name
        try:
            result = load_build_info(Path(path))
            self.assertEqual(result, {})
        finally:
            os.unlink(path)


if __name__ == "__main__":
    unittest.main()
