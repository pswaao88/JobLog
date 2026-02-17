from __future__ import annotations

from datetime import datetime
from typing import Any, Literal

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.core.db import get_db

router = APIRouter(prefix="/applications", tags=["applications"])

ApplicationStatus = Literal["planned", "applied", "interview", "rejected", "pass"]


class ApplicationUpsert(BaseModel):
    status: ApplicationStatus
    applied_at: datetime | None = None
    note: str | None = None


@router.put("/{job_id}")
def upsert_application(job_id: int, payload: ApplicationUpsert, db: Session = Depends(get_db)) -> dict[str, Any]:
    job_exists = db.execute(text("SELECT 1 FROM jobs WHERE id = :job_id"), {"job_id": job_id}).scalar()
    if not job_exists:
        raise HTTPException(status_code=404, detail="Job not found")

    row = db.execute(
        text(
            """
            INSERT INTO applications (job_id, status, applied_at, note, updated_at)
            VALUES (:job_id, :status, :applied_at, :note, NOW())
            ON CONFLICT (job_id)
            DO UPDATE SET
              status = EXCLUDED.status,
              applied_at = EXCLUDED.applied_at,
              note = EXCLUDED.note,
              updated_at = NOW()
            RETURNING id, job_id, status, applied_at, note, updated_at
            """
        ),
        {
            "job_id": job_id,
            "status": payload.status,
            "applied_at": payload.applied_at,
            "note": payload.note,
        },
    ).mappings().one()
    db.commit()

    return {
        "id": row["id"],
        "job_id": row["job_id"],
        "status": row["status"],
        "applied_at": row["applied_at"].isoformat() if row["applied_at"] else None,
        "note": row["note"],
        "updated_at": row["updated_at"].isoformat() if row["updated_at"] else None,
    }


@router.get("")
def list_applications(db: Session = Depends(get_db)) -> dict[str, Any]:
    rows = db.execute(
        text(
            """
            SELECT
              a.id,
              a.job_id,
              a.status,
              a.applied_at,
              a.note,
              a.updated_at,
              j.title,
              j.company_name,
              j.canonical_url AS url
            FROM applications a
            JOIN jobs j ON j.id = a.job_id
            ORDER BY a.updated_at DESC
            """
        )
    ).mappings().all()

    items = [
        {
            "id": row["id"],
            "job_id": row["job_id"],
            "status": row["status"],
            "applied_at": row["applied_at"].isoformat() if row["applied_at"] else None,
            "note": row["note"],
            "updated_at": row["updated_at"].isoformat() if row["updated_at"] else None,
            "title": row["title"],
            "company_name": row["company_name"],
            "url": row["url"],
        }
        for row in rows
    ]

    return {"items": items, "total": len(items)}
