from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles


from app.api.v1.admin import router as admin_router
from app.api.v1.applications import router as applications_router
from app.api.v1.bookmarks import router as bookmarks_router
from app.api.v1.health import router as health_router
from app.api.v1.jobs import router as jobs_router
from app.core.config import get_settings
from app.core.db import check_db_connection
from app.workers.scheduler import start_scheduler, stop_scheduler

settings = get_settings()
app = FastAPI(title=settings.app_name)
app.include_router(health_router, prefix="/api/v1")
app.include_router(jobs_router, prefix="/api/v1")
app.include_router(admin_router, prefix="/api/v1")
app.include_router(bookmarks_router, prefix="/api/v1")
app.include_router(applications_router, prefix="/api/v1")
frontend_dir = Path(__file__).resolve().parent / "frontend"
app.mount("/frontend", StaticFiles(directory=frontend_dir), name="frontend")


@app.on_event("startup")
def on_startup() -> None:
    try:
        check_db_connection()
        print("[startup] database connection check: ok")
    except Exception as exc:  # startup should continue for initial local setup
        print(f"[startup] database connection check failed: {exc}")

    if settings.scheduler_enabled:
        start_scheduler()
        print("[startup] scheduler started")


@app.on_event("shutdown")
def on_shutdown() -> None:
    if settings.scheduler_enabled:
        stop_scheduler()
        print("[shutdown] scheduler stopped")
main

@app.get("/")
def root() -> JSONResponse:
    return JSONResponse(
        {
            "service": settings.app_name,
            "env": settings.app_env,
            "docs": "/docs",
            "health": "/api/v1/health",
            "ui": "/ui",
        }
    )


@app.get("/ui")
def ui() -> FileResponse:
    return FileResponse(frontend_dir / "index.html")