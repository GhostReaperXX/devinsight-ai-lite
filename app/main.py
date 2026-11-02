"""Create the FastAPI application and connect its parts."""

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse, Response
from fastapi.staticfiles import StaticFiles

from app.database import Base, engine
from app.errors import AppError, ConflictError, NotFoundError, RuleViolationError
from app.routers import issues, pages, projects, users
from app.templating import templates

# The one place where business errors are translated into HTTP status codes.
ERROR_STATUS_CODES = {
    NotFoundError: 404,
    ConflictError: 409,
    RuleViolationError: 422,
}


@asynccontextmanager
async def lifespan(_app: FastAPI) -> AsyncIterator[None]:
    """Code before the yield runs once at startup, code after it at shutdown."""
    Base.metadata.create_all(engine)
    yield


app = FastAPI(
    title="DevInsight AI Lite",
    description="An intelligent software issue tracker.",
    version="0.4.0",
    lifespan=lifespan,
)

app.mount("/static", StaticFiles(directory="app/static"), name="static")

app.include_router(projects.router)
app.include_router(users.router)
app.include_router(issues.router)
app.include_router(pages.router)


def wants_html(request: Request) -> bool:
    """API callers get JSON. People browsing the site get a readable page."""
    return not request.url.path.startswith("/api/") and "text/html" in request.headers.get(
        "accept", ""
    )


@app.exception_handler(AppError)
def handle_app_error(request: Request, error: AppError) -> Response:
    status_code = ERROR_STATUS_CODES.get(type(error), 400)
    if wants_html(request):
        return templates.TemplateResponse(
            request,
            "error.html",
            {
                "status_code": status_code,
                "heading": "That did not work",
                "message": str(error),
            },
            status_code=status_code,
        )
    return JSONResponse(status_code=status_code, content={"detail": str(error)})
