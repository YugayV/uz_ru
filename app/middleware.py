from starlette.middleware.base import BaseHTTPMiddleware
from fastapi import Request

class SimpleRateLimitMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        ip = request.client.host if request.client else 'unknown'
        # TODO: Replace with Redis-backed rate limiter in production
        # For now just log and forward
        print(f"[RateLimit] Request from {ip} to {request.url}")
        response = await call_next(request)
        return response
