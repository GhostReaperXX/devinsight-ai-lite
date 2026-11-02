"""An endpoint that hosting platforms and people can call to check the service."""

import logging

from fastapi import APIRouter, Request, Response, status
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError

from app.deps import DbSession

router = APIRouter(tags=["Operations"])
logger = logging.getLogger(__name__)


@router.get("/health", summary="Can the service do its work right now?")
def health(request: Request, response: Response, db: DbSession):
    try:
        db.execute(text("SELECT 1"))
        database_ok = True
    except SQLAlchemyError:
        logger.exception("Health check could not reach the database")
        database_ok = False

    # Without the database nothing works, so report failure. Without the model the
    # application still works with suggestions switched off, so report it and carry on.
    if not database_ok:
        response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE
    return {
        "status": "ok" if database_ok else "unavailable",
        "database": "ok" if database_ok else "unreachable",
        "model": "loaded" if request.app.state.predictor is not None else "not loaded",
        "version": request.app.version,
    }
