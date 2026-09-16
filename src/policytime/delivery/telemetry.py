"""Bounded request controls and operational telemetry; never log question text."""

import hashlib
import json
import logging
import secrets
import threading
import time
from collections import deque
from collections.abc import Awaitable, Callable

from prometheus_client import CollectorRegistry, Counter, Histogram
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse, Response
from starlette.types import ASGIApp, Message, Receive, Scope, Send

logger = logging.getLogger("policytime.requests")


class Metrics:
    def __init__(self) -> None:
        self.registry = CollectorRegistry()
        self.requests = Counter(
            "policytime_requests_total",
            "Completed HTTP requests",
            ["route", "status"],
            registry=self.registry,
        )
        self.latency = Histogram(
            "policytime_request_seconds",
            "HTTP response latency",
            ["route"],
            buckets=(0.05, 0.1, 0.5, 1, 2, 5, 10, 15, 25, 60),
            registry=self.registry,
        )
        self.answers = Counter(
            "policytime_answers_total",
            "Policy outcomes",
            ["outcome", "mode"],
            registry=self.registry,
        )
        self.tokens = Counter(
            "policytime_model_tokens_total",
            "Reported model tokens",
            ["direction"],
            registry=self.registry,
        )
        self.cost = Counter("policytime_model_cost_usd", "Model cost", registry=self.registry)


class RateLimiter:
    def __init__(self, requests_per_minute: int) -> None:
        self.limit = requests_per_minute
        self._clients: dict[str, deque[float]] = {}
        self._salt = secrets.token_bytes(32)
        self._lock = threading.Lock()

    def allow(self, client: str) -> bool:
        key = hashlib.sha256(self._salt + client.encode()).hexdigest()
        now = time.monotonic()
        with self._lock:
            if len(self._clients) >= 4000:
                self._clients = {
                    key: times
                    for key, times in self._clients.items()
                    if times and times[-1] > now - 60
                }
                if key not in self._clients and len(self._clients) >= 4000:
                    return False
            history = self._clients.setdefault(key, deque())
            while history and history[0] <= now - 60:
                history.popleft()
            if len(history) >= self.limit:
                return False
            history.append(now)
            return True


class RequestTelemetry(BaseHTTPMiddleware):
    def __init__(self, app: ASGIApp, metrics: Metrics) -> None:
        super().__init__(app)
        self.metrics = metrics

    async def dispatch(
        self,
        request: Request,
        call_next: Callable[[Request], Awaitable[Response]],
    ) -> Response:
        started = time.perf_counter()
        response = await call_next(request)
        route = str(getattr(request.scope.get("route"), "path", "unmatched"))
        elapsed = time.perf_counter() - started
        self.metrics.requests.labels(route, str(response.status_code)).inc()
        self.metrics.latency.labels(route).observe(elapsed)
        logger.info(
            json.dumps(
                {
                    "event": "request",
                    "route": route,
                    "status": response.status_code,
                    "elapsed_ms": round(elapsed * 1000, 2),
                }
            )
        )
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["Referrer-Policy"] = "same-origin"
        response.headers["Content-Security-Policy"] = (
            "default-src 'self'; script-src 'self'; style-src 'self'; "
            "img-src 'self' data:; connect-src 'self'; frame-ancestors 'none'; base-uri 'self'; "
            "form-action 'self'"
        )
        response.headers["Permissions-Policy"] = "camera=(), microphone=(), geolocation=()"
        if request.method == "POST":
            response.headers["Cache-Control"] = "no-store"
        return response


class BodyLimitMiddleware:
    def __init__(self, app: ASGIApp, max_bytes: int = 8192) -> None:
        self.app = app
        self.max_bytes = max_bytes

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http" or scope["method"] != "POST":
            await self.app(scope, receive, send)
            return
        messages: deque[Message] = deque()
        size = 0
        while True:
            message = await receive()
            if message["type"] == "http.disconnect":
                return
            size += len(message.get("body", b""))
            if size > self.max_bytes:
                await JSONResponse({"detail": "Request body is too large."}, status_code=413)(
                    scope,
                    receive,
                    send,
                )
                return
            messages.append(message)
            if not message.get("more_body", False):
                break

        async def replay() -> Message:
            if messages:
                return messages.popleft()
            return await receive()

        await self.app(scope, replay, send)
