"""Code that runs around every request."""

from fastapi import FastAPI, Request

from app.config import get_settings

# The documentation pages load scripts that this strict policy would block.
DOCUMENTATION_PATHS = ("/docs", "/redoc")

CONTENT_SECURITY_POLICY = (
    "default-src 'self'; "
    "script-src 'self' https://cdn.jsdelivr.net; "
    "style-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net; "
    "img-src 'self' data:; "
    "font-src 'self' https://cdn.jsdelivr.net; "
    "connect-src 'self' https://cdn.jsdelivr.net; "
    "object-src 'none'; base-uri 'self'; form-action 'self'; frame-ancestors 'none'"
)


def register_middleware(app: FastAPI) -> None:
    @app.middleware("http")
    async def add_security_headers(request: Request, call_next):
        response = await call_next(request)
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        if not request.url.path.startswith(DOCUMENTATION_PATHS):
            response.headers["Content-Security-Policy"] = CONTENT_SECURITY_POLICY
        if get_settings().is_production:
            response.headers["Strict-Transport-Security"] = "max-age=31536000"
        return response
