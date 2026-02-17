from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.db import get_db
from app.services.classifier.rule_engine import classify_jobs
from app.services.crawler.runner import run_crawl

router = APIRouter(prefix="/admin", tags=["admin"])


@router.post("/crawl/run")
def trigger_crawl(
    source_code: str = Query(default="remotive"),
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    try:
        return run_crawl(db=db, source_code=source_code)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except RuntimeError as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@router.post("/classify/run")
def trigger_classification(
    rule_version: str | None = Query(default=None),
    limit: int = Query(default=200, ge=1, le=1000),
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    settings = get_settings()
    selected_rule_version = rule_version or settings.rule_version
    try:
        return classify_jobs(db=db, rule_version=selected_rule_version, limit=limit)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.get("/runs")
def list_runs(limit: int = Query(default=20, ge=1, le=100), db: Session = Depends(get_db)) -> dict[str, Any]:
    rows = db.execute(
        text(
            """
            SELECT
              cr.id,
              s.code AS source_code,
              cr.status::text AS status,
              cr.started_at,
              cr.finished_at,
              cr.fetched_count,
              cr.inserted_count,
              cr.updated_count,
              cr.failed_count,
              cr.error_message
            FROM crawl_runs cr
            LEFT JOIN sources s ON s.id = cr.source_id
            ORDER BY cr.started_at DESC
            LIMIT :limit
            """
        ),
        {"limit": limit},
    ).mappings().all()

    items = []
    for row in rows:
        items.append(
            {
                "id": row["id"],
                "source_code": row["source_code"],
                "status": row["status"],
                "started_at": row["started_at"].isoformat() if row["started_at"] else None,
                "finished_at": row["finished_at"].isoformat() if row["finished_at"] else None,
                "fetched_count": row["fetched_count"],
                "inserted_count": row["inserted_count"],
                "updated_count": row["updated_count"],
                "failed_count": row["failed_count"],
                "error_message": row["error_message"],
            }
        )

    return {"items": items, "limit": limit}
