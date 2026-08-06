"""
Rate limit middleware for FastAPI — Phase 07.
"""
from __future__ import annotations
import time
from collections import defaultdict
from fastapi import Request, HTTPException
from starlette.middleware.base import BaseHTTPMiddleware


class RateLimitMiddleware(BaseHTTPMiddleware):
    """
    Simple in-memory rate limiter.

    Write endpoints: 60 req/min/user.
    Read endpoints: 600 req/min/user.
    """

    WRITE_METHODS = {"POST", "PUT", "PATCH", "DELETE"}
    READ_METHODS = {"GET", "HEAD", "OPTIONS"}

    WRITE_LIMIT = 60
    READ_LIMIT = 600
    WINDOW_SECONDS = 60

    def __init__(self, app):
        super().__init__(app)
        self._buckets: dict[str, list[float]] = defaultdict(list)

    async def dispatch(self, request: Request, call_next):
        user_id = request.headers.get("x-user-id", request.client.host if request.client else "anonymous")
        method = request.method.upper()

        limit = self.WRITE_LIMIT if method in self.WRITE_METHODS else self.READ_LIMIT
        bucket_key = f"{user_id}:{method[0]}"  # user_id:R or user_id:W

        now = time.time()
        bucket = self._buckets[bucket_key]
        # Remove old entries
        cutoff = now - self.WINDOW_SECONDS
        self._buckets[bucket_key] = [t for t in bucket if t > cutoff]

        if len(self._buckets[bucket_key]) >= limit:
            raise HTTPException(429, f"Rate limit exceeded: {limit} req/min")

        self._buckets[bucket_key].append(now)

        return await call_next(request)


class CORSAllowListMiddleware(BaseHTTPMiddleware):
    """CORS middleware with allowlist from env."""

    def __init__(self, app, allowed_origins: list[str] | None = None):
        super().__init__(app)
        import os
        origins_env = os.environ.get("CORS_ALLOWED_ORIGINS", "*")
        self.allowed = allowed_origins or [o.strip() for o in origins_env.split(",") if o.strip()]

    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)
        origin = request.headers.get("origin", "")
        if "*" in self.allowed or origin in self.allowed:
            response.headers["Access-Control-Allow-Origin"] = origin if origin else "*"
            response.headers["Access-Control-Allow-Methods"] = "GET, POST, PUT, PATCH, DELETE, OPTIONS"
            response.headers["Access-Control-Allow-Headers"] = "Authorization, Content-Type"
        return response
