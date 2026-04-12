"""Tests for iCal parsing utilities in server.api.schedule."""

import unittest
from datetime import datetime


# Duplicated pure functions from backend.api.schedule to avoid full app import.

def _unfold_ical_lines(text: str) -> list[str]:
    lines = text.splitlines()
    unfolded: list[str] = []
    for line in lines:
        if line.startswith((" ", "\t")) and unfolded:
            unfolded[-1] += line[1:]
        else:
            unfolded.append(line)
    return unfolded


def _parse_ical_datetime(value: str) -> datetime | None:
    if not value:
        return None
    val = value.strip()
    if val.endswith("Z"):
        val = val[:-1]
    try:
        if "T" in val:
            return datetime.strptime(val, "%Y%m%dT%H%M%S")
        return datetime.strptime(val, "%Y%m%d")
    except Exception:
        return None


def _parse_ical_events(text: str) -> list[dict]:
    lines = _unfold_ical_lines(text)
    events: list[dict] = []
    current: dict | None = None
    for line in lines:
        if line == "BEGIN:VEVENT":
            current = {}
            continue
        if line == "END:VEVENT":
            if current is not None:
                events.append(current)
            current = None
            continue
        if current is None or ":" not in line:
            continue
        key, value = line.split(":", 1)
        key = key.split(";", 1)[0].upper()
        value = value.replace("\\n", "\n").strip()
        current[key] = value
    return events


class TestUnfoldIcalLines(unittest.TestCase):
    def test_no_folding(self):
        text = "LINE1\nLINE2\nLINE3"
        self.assertEqual(_unfold_ical_lines(text), ["LINE1", "LINE2", "LINE3"])

    def test_space_continuation(self):
        text = "LONG\n LINE"
        self.assertEqual(_unfold_ical_lines(text), ["LONGLINE"])

    def test_tab_continuation(self):
        text = "LONG\n\tLINE"
        self.assertEqual(_unfold_ical_lines(text), ["LONGLINE"])

    def test_multiple_continuations(self):
        text = "A\n B\n C"
        self.assertEqual(_unfold_ical_lines(text), ["ABC"])

    def test_empty_input(self):
        self.assertEqual(_unfold_ical_lines(""), [])

    def test_mixed_folded_and_normal(self):
        text = "FIRST\n CONTINUED\nSECOND\nTHIRD\n CONT"
        result = _unfold_ical_lines(text)
        self.assertEqual(result, ["FIRSTCONTINUED", "SECOND", "THIRDCONT"])


class TestParseIcalDatetime(unittest.TestCase):
    def test_datetime_with_time(self):
        result = _parse_ical_datetime("20240615T143000")
        self.assertEqual(result, datetime(2024, 6, 15, 14, 30, 0))

    def test_datetime_with_z(self):
        result = _parse_ical_datetime("20240615T143000Z")
        self.assertEqual(result, datetime(2024, 6, 15, 14, 30, 0))

    def test_date_only(self):
        result = _parse_ical_datetime("20240615")
        self.assertEqual(result, datetime(2024, 6, 15, 0, 0, 0))

    def test_empty_string(self):
        self.assertIsNone(_parse_ical_datetime(""))

    def test_invalid_format(self):
        self.assertIsNone(_parse_ical_datetime("not-a-date"))

    def test_whitespace_stripped(self):
        result = _parse_ical_datetime("  20240615T100000Z  ")
        self.assertEqual(result, datetime(2024, 6, 15, 10, 0, 0))


class TestParseIcalEvents(unittest.TestCase):
    def test_single_event(self):
        ical = (
            "BEGIN:VCALENDAR\n"
            "BEGIN:VEVENT\n"
            "SUMMARY:Лекция\n"
            "DTSTART:20240615T090000Z\n"
            "DTEND:20240615T103000Z\n"
            "LOCATION:А-123\n"
            "END:VEVENT\n"
            "END:VCALENDAR"
        )
        events = _parse_ical_events(ical)
        self.assertEqual(len(events), 1)
        self.assertEqual(events[0]["SUMMARY"], "Лекция")
        self.assertEqual(events[0]["LOCATION"], "А-123")

    def test_multiple_events(self):
        ical = (
            "BEGIN:VEVENT\nSUMMARY:First\nEND:VEVENT\n"
            "BEGIN:VEVENT\nSUMMARY:Second\nEND:VEVENT"
        )
        events = _parse_ical_events(ical)
        self.assertEqual(len(events), 2)
        self.assertEqual(events[0]["SUMMARY"], "First")
        self.assertEqual(events[1]["SUMMARY"], "Second")

    def test_no_events(self):
        self.assertEqual(_parse_ical_events("BEGIN:VCALENDAR\nEND:VCALENDAR"), [])

    def test_empty_input(self):
        self.assertEqual(_parse_ical_events(""), [])

    def test_key_with_params_stripped(self):
        ical = "BEGIN:VEVENT\nDTSTART;VALUE=DATE:20240615\nEND:VEVENT"
        events = _parse_ical_events(ical)
        self.assertEqual(events[0]["DTSTART"], "20240615")

    def test_escaped_newlines(self):
        ical = "BEGIN:VEVENT\nDESCRIPTION:Line1\\nLine2\nEND:VEVENT"
        events = _parse_ical_events(ical)
        self.assertEqual(events[0]["DESCRIPTION"], "Line1\nLine2")

    def test_folded_lines_in_event(self):
        ical = "BEGIN:VEVENT\nSUMMARY:Very long\n  summary text\nEND:VEVENT"
        events = _parse_ical_events(ical)
        self.assertEqual(events[0]["SUMMARY"], "Very long summary text")


class TestParseIcalDatetimeEdgeCases(unittest.TestCase):
    def test_midnight(self):
        result = _parse_ical_datetime("20240101T000000")
        self.assertEqual(result, datetime(2024, 1, 1, 0, 0, 0))

    def test_end_of_day(self):
        result = _parse_ical_datetime("20241231T235959")
        self.assertEqual(result, datetime(2024, 12, 31, 23, 59, 59))


if __name__ == "__main__":
    unittest.main()
