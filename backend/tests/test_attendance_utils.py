"""Tests for _normalize_friend_ids from backend.api.attendance."""

import unittest


def _normalize_friend_ids(raw_ids, *, max_items: int = 20) -> tuple[list[int], str | None]:
    if raw_ids is None:
        return [], None
    if not isinstance(raw_ids, list):
        return [], "friend_ids должен быть массивом"
    if len(raw_ids) > max_items:
        return [], f"Можно выбрать не более {max_items} друзей за раз"
    normalized: list[int] = []
    seen: set[int] = set()
    for raw in raw_ids:
        if isinstance(raw, bool):
            return [], "Некорректный friend_id"
        if isinstance(raw, int):
            fid = raw
        elif isinstance(raw, str) and raw.isdigit():
            fid = int(raw)
        else:
            return [], "Некорректный friend_id"
        if fid <= 0:
            return [], "Некорректный friend_id"
        if fid in seen:
            continue
        seen.add(fid)
        normalized.append(fid)
    return normalized, None


class TestNormalizeFriendIds(unittest.TestCase):
    def test_none_returns_empty(self):
        ids, err = _normalize_friend_ids(None)
        self.assertEqual(ids, [])
        self.assertIsNone(err)

    def test_not_a_list(self):
        ids, err = _normalize_friend_ids("not a list")
        self.assertEqual(ids, [])
        self.assertIn("массивом", err)

    def test_valid_ints(self):
        ids, err = _normalize_friend_ids([1, 2, 3])
        self.assertEqual(ids, [1, 2, 3])
        self.assertIsNone(err)

    def test_string_ints(self):
        ids, err = _normalize_friend_ids(["1", "2"])
        self.assertEqual(ids, [1, 2])
        self.assertIsNone(err)

    def test_duplicates_removed(self):
        ids, err = _normalize_friend_ids([5, 5, 5])
        self.assertEqual(ids, [5])
        self.assertIsNone(err)

    def test_zero_rejected(self):
        ids, err = _normalize_friend_ids([0])
        self.assertEqual(ids, [])
        self.assertIsNotNone(err)

    def test_negative_rejected(self):
        ids, err = _normalize_friend_ids([-1])
        self.assertEqual(ids, [])
        self.assertIsNotNone(err)

    def test_bool_rejected(self):
        ids, err = _normalize_friend_ids([True])
        self.assertEqual(ids, [])
        self.assertIn("Некорректный", err)

    def test_non_numeric_string_rejected(self):
        ids, err = _normalize_friend_ids(["abc"])
        self.assertEqual(ids, [])
        self.assertIsNotNone(err)

    def test_exceeds_max_items(self):
        ids, err = _normalize_friend_ids(list(range(1, 25)), max_items=20)
        self.assertEqual(ids, [])
        self.assertIn("20", err)

    def test_custom_max_items(self):
        ids, err = _normalize_friend_ids([1, 2, 3], max_items=2)
        self.assertEqual(ids, [])
        self.assertIn("2", err)

    def test_empty_list(self):
        ids, err = _normalize_friend_ids([])
        self.assertEqual(ids, [])
        self.assertIsNone(err)

    def test_mixed_valid(self):
        ids, err = _normalize_friend_ids([1, "2", 3])
        self.assertEqual(ids, [1, 2, 3])
        self.assertIsNone(err)


if __name__ == "__main__":
    unittest.main()
