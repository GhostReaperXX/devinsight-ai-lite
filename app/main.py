"""Create the FastAPI application and connect its parts."""

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from app.database import Base, engine
from app.errors import AppError, ConflictError, NotFoundError, RuleViolationError
from app.routers import issues, projects, users

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
    version="0.3.0",
    lifespan=lifespan,
)

app.include_router(projects.router)
app.include_router(users.router)
app.include_router(issues.router)


@app.exception_handler(AppError)
def handle_app_error(_request: Request, error: AppError) -> JSONResponse:
    status_code = ERROR_STATUS_CODES.get(type(error), 400)
    return JSONResponse(status_code=status_code, content={"detail": str(error)})
