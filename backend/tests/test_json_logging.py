import json
import logging
import sys
import unittest
import datetime


class _JSONFormatter(logging.Formatter):
    """Duplicated from server/main.py to test without importing the full app."""

    def format(self, record: logging.LogRecord) -> str:
        entry: dict = {
            "ts": datetime.datetime.utcnow().isoformat(timespec="milliseconds") + "Z",
            "level": record.levelname,
            "logger": record.name,
            "msg": record.getMessage(),
        }
        if hasattr(record, "request_id"):
            entry["request_id"] = record.request_id
        if record.exc_info and record.exc_info[1]:
            entry["exception"] = self.formatException(record.exc_info)
        return json.dumps(entry, ensure_ascii=False)


class TestJSONFormatter(unittest.TestCase):
    def setUp(self):
        self.formatter = _JSONFormatter()

    def _make_record(self, msg="test", level=logging.INFO, **extra):
        record = logging.LogRecord(
            name="test.logger",
            level=level,
            pathname="",
            lineno=0,
            msg=msg,
            args=(),
            exc_info=None,
        )
        for k, v in extra.items():
            setattr(record, k, v)
        return record

    def test_output_is_json(self):
        record = self._make_record("hello")
        output = self.formatter.format(record)
        data = json.loads(output)
        self.assertEqual(data["msg"], "hello")
        self.assertEqual(data["level"], "INFO")
        self.assertEqual(data["logger"], "test.logger")

    def test_includes_ts(self):
        record = self._make_record()
        data = json.loads(self.formatter.format(record))
        self.assertIn("ts", data)
        self.assertTrue(data["ts"].endswith("Z"))

    def test_includes_request_id_when_present(self):
        record = self._make_record(request_id="abc123")
        data = json.loads(self.formatter.format(record))
        self.assertEqual(data["request_id"], "abc123")

    def test_excludes_request_id_when_absent(self):
        record = self._make_record()
        data = json.loads(self.formatter.format(record))
        self.assertNotIn("request_id", data)

    def test_warning_level(self):
        record = self._make_record(level=logging.WARNING)
        data = json.loads(self.formatter.format(record))
        self.assertEqual(data["level"], "WARNING")

    def test_cyrillic_message(self):
        record = self._make_record("Привет мир")
        output = self.formatter.format(record)
        data = json.loads(output)
        self.assertEqual(data["msg"], "Привет мир")

    def test_exception_included(self):
        try:
            raise ValueError("test error")
        except ValueError:
            record = self._make_record()
            record.exc_info = sys.exc_info()
        data = json.loads(self.formatter.format(record))
        self.assertIn("exception", data)
        self.assertIn("ValueError", data["exception"])


if __name__ == "__main__":
    unittest.main()
