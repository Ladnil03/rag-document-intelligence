"""Health and liveness/readiness probes."""

from fastapi import APIRouter, HTTPException, status
from fastapi.responses import JSONResponse

from app.core import config
from app.core.storage import storage_is_writable
from app.db.base import check_database_connection

router = APIRouter(tags=["Health"])


@router.get("/", include_in_schema=False)
def hello():
    return {"message": "RAG Document Intelligence API", "environment": config.ENVIRONMENT}


@router.get("/health")
def health_check():
    """Detailed health report of application and underlying dependencies."""
    db_ok, db_msg = check_database_connection()
    storage_ok = storage_is_writable()

    is_healthy = db_ok and storage_ok
    status_code = status.HTTP_200_OK if is_healthy else status.HTTP_503_SERVICE_UNAVAILABLE

    return JSONResponse(
        status_code=status_code,
        content={
            "status": "healthy" if is_healthy else "unhealthy",
            "environment": config.ENVIRONMENT,
            "components": {
                "database": {"status": "ok" if db_ok else "error", "message": db_msg},
                "storage": {"status": "ok" if storage_ok else "error", "path": config.STORAGE_DIR},
            },
        },
    )


@router.get("/health/liveness")
def liveness_probe():
    return {"status": "alive"}


@router.get("/health/readiness")
def readiness_probe():
    db_ok, db_msg = check_database_connection()
    if not db_ok:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Service not ready: {db_msg}",
        )
    return {"status": "ready", "database": "connected"}
