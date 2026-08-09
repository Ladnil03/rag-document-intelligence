"""
FastAPI application entry point.

This module wires the modular routers together, registers the global
exception handler, configures CORS, and defines the lifespan hook that
initialises the database. All actual logic lives under ``app.api.routes``
and ``app.services``; this file is intentionally small.

``uvicorn main:app`` from the ``backend/`` directory still works because
``backend/main.py`` is a one-line shim that imports ``app`` from here.
"""

import logging
import os
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api.routes import auth, chat, conversations, documents, health, query
from app.core import config
from app.core.storage import ensure_storage_dir
from app.db.base import Base, engine
from app.db.migrations import migrate_phase5_schema
from app.models import *  # noqa: F401,F403  -- register all models with Base.metadata


logging.basicConfig(
    level=getattr(logging, config.LOG_LEVEL, logging.INFO),
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger("rag_platform")


def _init_db() -> None:
    try:
        Base.metadata.create_all(bind=engine)
        migrate_phase5_schema()
    except Exception as exc:
        logger.warning("Could not initialise database tables: %s", exc)


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info(
        "Starting RAG Document Intelligence Platform (environment=%s)",
        config.ENVIRONMENT,
    )
    ensure_storage_dir()
    _init_db()
    yield
    logger.info("Shutting down RAG Document Intelligence Platform cleanly.")


app = FastAPI(
    title="RAG Document Intelligence Platform",
    description="Enterprise-grade document RAG backend with multi-tenant isolation, streaming conversations, and evaluation.",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=config.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Routers — order does not matter; FastAPI matches by path.
app.include_router(auth.router)
app.include_router(documents.router)
app.include_router(conversations.router)
app.include_router(chat.router)
app.include_router(query.router)
app.include_router(health.router)


@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception):
    """Global error handler: log full traceback, return sanitised 500."""
    logger.error(
        "Unhandled exception on %s %s: %s",
        request.method,
        request.url.path,
        exc,
        exc_info=True,
    )
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"detail": "An internal server error occurred."},
    )
