"""Turn every kind of failure into a safe, helpful answer for API clients and browsers."""

import logging
from urllib.parse import quote

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse, RedirectResponse, Response
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.deps import LoginRequired
from app.errors import (
    AppError,
    AuthenticationError,
    ConflictError,
    NotFoundError,
    PermissionDeniedError,
    RuleViolationError,
)
from app.templating import templates

logger = logging.getLogger(__name__)

# The one place where business errors are translated into HTTP status codes.
ERROR_STATUS_CODES = {
    NotFoundError: 404,
    ConflictError: 409,
    RuleViolationError: 422,
    PermissionDeniedError: 403,
    AuthenticationError: 401,
}

HEADINGS = {
    401: "Please log in",
    403: "You do not have permission to do this",
    404: "We could not find that page",
    409: "That clashes with existing data",
    422: "That request could not be processed",
    500: "Something went wrong on our side",
}


def wants_html(request: Request) -> bool:
    """API callers get JSON. People browsing the site get a readable page."""
    return not request.url.path.startswith("/api/") and "text/html" in request.headers.get(
        "accept", ""
    )


def error_page(request: Request, status_code: int, message: str) -> Response:
    return templates.TemplateResponse(
        request,
        "error.html",
        {
            "status_code": status_code,
            "heading": HEADINGS.get(status_code, "That did not work"),
            "message": message,
        },
        status_code=status_code,
    )


def register_error_handlers(app: FastAPI) -> None:
    @app.exception_handler(LoginRequired)
    def handle_login_required(_request: Request, error: LoginRequired) -> Response:
        return RedirectResponse(f"/login?next={quote(error.next_path)}", status_code=303)

    @app.exception_handler(AppError)
    def handle_app_error(request: Request, error: AppError) -> Response:
        status_code = ERROR_STATUS_CODES.get(type(error), 400)
        if wants_html(request):
            return error_page(request, status_code, str(error))
        return JSONResponse(status_code=status_code, content={"detail": str(error)})

    @app.exception_handler(StarletteHTTPException)
    def handle_http_exception(request: Request, error: StarletteHTTPException) -> Response:
        if wants_html(request):
            return error_page(request, error.status_code, str(error.detail))
        return JSONResponse(
            status_code=error.status_code,
            content={"detail": error.detail},
            headers=getattr(error, "headers", None),
        )

    @app.exception_handler(RequestValidationError)
    def handle_validation_error(
        request: Request, error: RequestValidationError
    ) -> Response:
        if wants_html(request):
            return error_page(
                request, 422, "Some of the values in the address are not valid."
            )
        # Only the location and the message: echoing the input could reflect secrets.
        details = [{"loc": item["loc"], "msg": item["msg"]} for item in error.errors()]
        return JSONResponse(status_code=422, content={"detail": details})

    @app.exception_handler(Exception)
    def handle_unexpected_error(request: Request, error: Exception) -> Response:
        # The full detail goes to the log for developers. The user sees nothing internal.
        # This handler runs on a worker thread where no exception is active, so pass it in.
        logger.error(
            "Unhandled error on %s %s", request.method, request.url.path, exc_info=error
        )
        if wants_html(request):
            return error_page(
                request,
                500,
                "Please try again. If it keeps happening, tell an administrator.",
            )
        return JSONResponse(status_code=500, content={"detail": "Internal server error."})
