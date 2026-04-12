import asyncio
import logging
from pathlib import Path
from urllib.parse import urlparse

from aiohttp import web
import aiohttp_cors

from backend.config import settings
from backend.database import init_db
from backend.services.api_middlewares import json_error_middleware, rate_limit_middleware, request_id_middleware
from backend.api.routes import setup_routes

import json as _json
import datetime as _dt


class _JSONFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        entry: dict = {
            "ts": _dt.datetime.now(_dt.timezone.utc).isoformat(timespec="milliseconds").replace("+00:00", "Z"),
            "level": record.levelname,
            "logger": record.name,
            "msg": record.getMessage(),
        }
        if hasattr(record, "request_id"):
            entry["request_id"] = record.request_id
        if record.exc_info and record.exc_info[1]:
            entry["exception"] = self.formatException(record.exc_info)
        return _json.dumps(entry, ensure_ascii=False)


_handler = logging.StreamHandler()
_handler.setFormatter(_JSONFormatter())
logging.root.handlers = [_handler]
logging.root.setLevel(logging.INFO)
logger = logging.getLogger(__name__)


def _build_cors_defaults() -> dict:
    allowed: set[str] = set()

    webapp_url = (getattr(settings, "webapp_url", "") or "").strip()
    if webapp_url:
        try:
            parsed = urlparse(webapp_url)
            if parsed.scheme and parsed.netloc:
                allowed.add(f"{parsed.scheme}://{parsed.netloc}")
        except Exception:
            pass

    allowed.update({
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    })

    if not allowed or (len(allowed) == 4 and not webapp_url):
        logger.warning("CORS: WEBAPP_URL missing/invalid, using localhost-only origins")

    opts = aiohttp_cors.ResourceOptions(
        allow_credentials=True,
        expose_headers=("Content-Type", "Content-Length", "X-Request-Id"),
        allow_headers=("Content-Type", "Authorization", "X-Request-Id"),
        allow_methods=("GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"),
    )
    return {origin: opts for origin in sorted(allowed)}


async def main():
    Path("data").mkdir(exist_ok=True)

    await init_db()
    logger.info("Database initialized")

    app = web.Application(
        client_max_size=10 * 1024 * 1024,  # 10 MB max request body
        middlewares=[
            request_id_middleware,
            json_error_middleware,
            rate_limit_middleware,
        ],
    )
    app["started_monotonic"] = asyncio.get_running_loop().time()
    setup_routes(app)
    cors = aiohttp_cors.setup(app, defaults=_build_cors_defaults())
    for route in list(app.router.routes()):
        cors.add(route)

    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, settings.api_bind_host, int(settings.api_port))

    logger.info(f"Starting API server on {settings.api_bind_host}:{int(settings.api_port)}...")
    await site.start()

    # Run forever
    await asyncio.Event().wait()


if __name__ == "__main__":
    asyncio.run(main())
