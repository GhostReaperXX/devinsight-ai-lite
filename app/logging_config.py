"""One logging setup for the whole application."""

import logging

from app.config import get_settings


def configure_logging() -> None:
    logging.basicConfig(
        level=get_settings().log_level,
        format="%(asctime)s %(levelname)-7s %(name)s: %(message)s",
    )
    # Our own request log below replaces uvicorn's, so each request is logged once.
    logging.getLogger("uvicorn.access").disabled = True
