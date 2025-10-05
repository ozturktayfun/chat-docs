from __future__ import annotations

import logging
from typing import Any

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api import router as api_router
from app.core.config import get_settings
from app.core.logging import configure_logging
from app.db.mongodb import close_mongo_connection, connect_to_mongo
from app.db.postgres import init_db

settings = get_settings()
configure_logging("DEBUG" if settings.debug else "INFO")
logger = logging.getLogger(__name__)

app = FastAPI(
    title=settings.app_name,
    version=settings.version,
    docs_url="/docs",
    redoc_url="/redoc",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
async def on_startup() -> None:
    """Initialise database connections."""

    logger.info("Starting Document Chat Assistant")
    init_db()
    await connect_to_mongo()


@app.on_event("shutdown")
async def on_shutdown() -> None:
    """Cleanly close resources on shutdown."""

    logger.info("Shutting down Document Chat Assistant")
    await close_mongo_connection()


@app.get("/health", tags=["system"])
async def health_check() -> dict[str, Any]:
    """Basic health-check endpoint."""

    return {
        "status": "ok",
        "app": settings.app_name,
        "version": settings.version,
    }


app.include_router(api_router)
