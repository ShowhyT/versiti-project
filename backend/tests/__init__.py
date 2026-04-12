import os
import sys

os.environ.setdefault("JWT_SECRET", "test-jwt-secret")
os.environ.setdefault("WEBAPP_URL", "http://localhost:5173")
os.environ.setdefault("DATABASE_URL", "sqlite+aiosqlite:///./data/test.db")
os.environ.setdefault("SESSION_KEYS", "test-session-key")

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
