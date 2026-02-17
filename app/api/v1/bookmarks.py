from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.core.db import get_db

router = APIRouter(prefix="/bookmarks", tags=["bookmarks"])


class BookmarkCreate(BaseModel):
    job_id: int
    memo: str | None = None


@router.post("")
def create_bookmark(payload: BookmarkCreate, db: Session = Depends(get_db)) -> dict[str, Any]:
    job_exists = db.execute(text("SELECT 1 FROM jobs WHERE id = :job_id"), {"job_id": payload.job_id}).scalar()
    if not job_exists:
        raise HTTPException(status_code=404, detail="Job not found")

    row = db.execute(
        text(
            """
            INSERT INTO bookmarks (job_id, memo, created_at)
            VALUES (:job_id, :memo, NOW())
            ON CONFLICT (job_id)
            DO UPDATE SET memo = EXCLUDED.memo
            RETURNING id, job_id, memo, created_at
            """
        ),
        {"job_id": payload.job_id, "memo": payload.memo},
    ).mappings().one()
    db.commit()

    return {
        "id": row["id"],
        "job_id": row["job_id"],
        "memo": row["memo"],
        "created_at": row["created_at"].isoformat() if row["created_at"] else None,
    }


@router.get("")
def list_bookmarks(db: Session = Depends(get_db)) -> dict[str, Any]:
    rows = db.execute(
        text(
            """
            SELECT
              b.id,
              b.job_id,
              b.memo,
              b.created_at,
              j.title,
              j.company_name,
              j.canonical_url AS url
            FROM bookmarks b
            JOIN jobs j ON j.id = b.job_id
            ORDER BY b.created_at DESC
            """
        )
    ).mappings().all()

    items = [
        {
            "id": row["id"],
            "job_id": row["job_id"],
            "memo": row["memo"],
            "created_at": row["created_at"].isoformat() if row["created_at"] else None,
            "title": row["title"],
            "company_name": row["company_name"],
            "url": row["url"],
        }
        for row in rows
    ]
    return {"items": items, "total": len(items)}


@router.delete("/{job_id}")
def delete_bookmark(job_id: int, db: Session = Depends(get_db)) -> dict[str, Any]:
    deleted = db.execute(
        text("DELETE FROM bookmarks WHERE job_id = :job_id RETURNING job_id"),
        {"job_id": job_id},
    ).scalar()
    db.commit()
    if deleted is None:
        raise HTTPException(status_code=404, detail="Bookmark not found")
    return {"deleted": True, "job_id": job_id}
