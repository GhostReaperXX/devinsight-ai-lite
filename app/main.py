"""Create the FastAPI application and connect its parts."""

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from app.config import get_settings
from app.database import Base, engine
from app.error_handlers import register_error_handlers
from app.logging_config import configure_logging
from app.middleware import register_middleware
from app.ml.predictor import CategoryPredictor
from app.routers import auth, health, insights, issues, pages, projects, users

configure_logging()


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    """Code before the yield runs once at startup, code after it at shutdown."""
    Base.metadata.create_all(engine)
    # Loaded once here, because reading the file on every request would be far too slow.
    app.state.predictor = CategoryPredictor.load(get_settings().classifier_file)
    yield


app = FastAPI(
    title="DevInsight AI Lite",
    description="An intelligent software issue tracker.",
    version="0.7.0",
    lifespan=lifespan,
)

app.mount("/static", StaticFiles(directory="app/static"), name="static")

app.include_router(health.router)
app.include_router(auth.router)
app.include_router(projects.router)
app.include_router(users.router)
app.include_router(issues.router)
app.include_router(insights.router)
app.include_router(pages.router)

register_error_handlers(app)
register_middleware(app)
