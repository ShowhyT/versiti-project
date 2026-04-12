"""Tests for pure utility functions in server.api.profile (no DB required)."""

import unittest

# Duplicated constants & functions to avoid importing server.api.profile
# (which triggers DB init via require_user imports).

VALID_THEMES = {"dark", "light", "ocean"}
KNOWN_TABS = {"feed", "scanner", "schedule", "grades", "passes", "maps", "esports"}
FIXED_TABS = {"feed", "scanner", "schedule", "grades", "passes"}
MAX_TABS = 7


def _parse_visible_tabs(raw: str | None) -> list[str] | None:
    import json
    if not raw:
        return None
    try:
        tabs = json.loads(raw)
        if isinstance(tabs, list):
            return [t for t in tabs if t in KNOWN_TABS]
    except (json.JSONDecodeError, TypeError):
        pass
    return None


def _resolve_theme_mode(user) -> str:
    tm = getattr(user, "theme_mode", None)
    if tm and tm in VALID_THEMES:
        return tm
    return "light" if bool(getattr(user, "light_theme_enabled", False)) else "dark"


def _validate_visible_tabs(tabs: list) -> list[str] | None:
    if not isinstance(tabs, list):
        return None
    cleaned = []
    seen = set()
    for t in tabs:
        if isinstance(t, str) and t in KNOWN_TABS and t not in seen:
            cleaned.append(t)
            seen.add(t)
    for ft in FIXED_TABS:
        if ft not in seen:
            cleaned.append(ft)
    return cleaned[:MAX_TABS]


class TestParseVisibleTabs(unittest.TestCase):
    def test_none_returns_none(self):
        self.assertIsNone(_parse_visible_tabs(None))

    def test_empty_string_returns_none(self):
        self.assertIsNone(_parse_visible_tabs(""))

    def test_valid_json_array(self):
        result = _parse_visible_tabs('["feed", "maps", "esports"]')
        self.assertEqual(result, ["feed", "maps", "esports"])

    def test_filters_unknown_tabs(self):
        result = _parse_visible_tabs('["feed", "unknown", "maps"]')
        self.assertEqual(result, ["feed", "maps"])

    def test_invalid_json(self):
        self.assertIsNone(_parse_visible_tabs("{broken"))

    def test_json_object_returns_none(self):
        self.assertIsNone(_parse_visible_tabs('{"key": "value"}'))

    def test_json_string_returns_none(self):
        self.assertIsNone(_parse_visible_tabs('"just a string"'))


class TestResolveThemeMode(unittest.TestCase):
    def _user(self, **attrs):
        class U:
            pass
        u = U()
        for k, v in attrs.items():
            setattr(u, k, v)
        return u

    def test_explicit_dark(self):
        self.assertEqual(_resolve_theme_mode(self._user(theme_mode="dark")), "dark")

    def test_explicit_light(self):
        self.assertEqual(_resolve_theme_mode(self._user(theme_mode="light")), "light")

    def test_explicit_ocean(self):
        self.assertEqual(_resolve_theme_mode(self._user(theme_mode="ocean")), "ocean")

    def test_invalid_theme_falls_back_to_dark(self):
        self.assertEqual(_resolve_theme_mode(self._user(theme_mode="neon")), "dark")

    def test_none_theme_with_light_enabled(self):
        self.assertEqual(
            _resolve_theme_mode(self._user(theme_mode=None, light_theme_enabled=True)),
            "light",
        )

    def test_none_theme_with_light_disabled(self):
        self.assertEqual(
            _resolve_theme_mode(self._user(theme_mode=None, light_theme_enabled=False)),
            "dark",
        )

    def test_no_attrs_at_all(self):
        self.assertEqual(_resolve_theme_mode(self._user()), "dark")


class TestValidateVisibleTabs(unittest.TestCase):
    def test_not_a_list(self):
        self.assertIsNone(_validate_visible_tabs("feed"))
        self.assertIsNone(_validate_visible_tabs(42))

    def test_empty_list_gets_fixed_tabs(self):
        result = _validate_visible_tabs([])
        self.assertIsNotNone(result)
        for ft in FIXED_TABS:
            self.assertIn(ft, result)

    def test_valid_tabs_preserved(self):
        result = _validate_visible_tabs(["maps", "esports", "feed", "scanner", "schedule", "grades", "passes"])
        self.assertEqual(len(result), 7)
        self.assertEqual(result[0], "maps")  # user order first
        self.assertEqual(result[1], "esports")

    def test_duplicates_removed(self):
        result = _validate_visible_tabs(["feed", "feed", "feed"])
        self.assertEqual(result.count("feed"), 1)

    def test_unknown_tabs_filtered(self):
        result = _validate_visible_tabs(["feed", "invalid", "maps"])
        self.assertNotIn("invalid", result)
        self.assertIn("feed", result)
        self.assertIn("maps", result)

    def test_max_tabs_enforced(self):
        all_known = list(KNOWN_TABS)
        result = _validate_visible_tabs(all_known)
        self.assertLessEqual(len(result), MAX_TABS)

    def test_non_string_items_ignored(self):
        result = _validate_visible_tabs(["feed", 42, None, "maps"])
        self.assertIn("feed", result)
        self.assertIn("maps", result)


if __name__ == "__main__":
    unittest.main()
