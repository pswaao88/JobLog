from fastapi import FastAPI
from fastapi.responses import JSONResponse

from app.api.v1.health import router as health_router
from app.core.config import get_settings
from app.core.db import check_db_connection

settings = get_settings()
app = FastAPI(title=settings.app_name)
app.include_router(health_router, prefix="/api/v1")


@app.on_event("startup")
def on_startup() -> None:
    try:
        check_db_connection()
        print("[startup] database connection check: ok")
    except Exception as exc:  # startup should continue for initial local setup
        print(f"[startup] database connection check failed: {exc}")


@app.get("/")
def root() -> JSONResponse:
    return JSONResponse(
        {
            "service": settings.app_name,
            "env": settings.app_env,
            "docs": "/docs",
            "health": "/api/v1/health",
        }
    )
