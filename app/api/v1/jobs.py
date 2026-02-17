from __future__ import annotations

from datetime import datetime, time, timezone
from typing import Any, Literal

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.db import get_db

router = APIRouter(prefix="/jobs", tags=["jobs"])

SortOption = Literal["posted_at_desc", "deadline_asc", "score_desc"]


def _to_iso(value: Any) -> str | None:
    if value is None:
        return None
    if isinstance(value, datetime):
        return value.isoformat()
    return str(value)


def _build_jobs_filters(
    employment_type: str | None,
    role_type: str | None,
    is_active: bool,
    q: str | None,
    posted_from: datetime | None,
    posted_to: datetime | None,
    deadline_before: datetime | None,
) -> tuple[list[str], dict[str, Any]]:
    where_clauses = ["j.is_active = :is_active"]
    params: dict[str, Any] = {"is_active": is_active}

    if employment_type:
        where_clauses.append("jc.employment_type = :employment_type")
        params["employment_type"] = employment_type

    if role_type:
        where_clauses.append("jc.role_type = :role_type")
        params["role_type"] = role_type

    if q:
        where_clauses.append("(j.company_name ILIKE :q OR j.title ILIKE :q)")
        params["q"] = f"%{q}%"

    if posted_from:
        where_clauses.append("j.posted_at >= :posted_from")
        params["posted_from"] = posted_from

    if posted_to:
        where_clauses.append("j.posted_at <= :posted_to")
        params["posted_to"] = posted_to

    if deadline_before:
        where_clauses.append("j.deadline_at <= :deadline_before")
        params["deadline_before"] = deadline_before

    return where_clauses, params


def _sort_clause(sort: SortOption) -> str:
    if sort == "deadline_asc":
        return "j.deadline_at ASC NULLS LAST"
    if sort == "score_desc":
        return "jc.new_grad_score DESC NULLS LAST, j.posted_at DESC NULLS LAST"
    return "j.posted_at DESC NULLS LAST"


@router.get("")
def list_jobs(
    employment_type: str | None = Query(default=None),
    role_type: str | None = Query(default="backend"),
    is_active: bool = Query(default=True),
    q: str | None = Query(default=None),
    posted_from: datetime | None = Query(default=None),
    posted_to: datetime | None = Query(default=None),
    deadline_before: datetime | None = Query(default=None),
    sort: SortOption = Query(default="posted_at_desc"),
    page: int = Query(default=1, ge=1),
    size: int = Query(default=20, ge=1, le=100),
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    settings = get_settings()
    where_clauses, params = _build_jobs_filters(
        employment_type=employment_type,
        role_type=role_type,
        is_active=is_active,
        q=q,
        posted_from=posted_from,
        posted_to=posted_to,
        deadline_before=deadline_before,
    )

    where_sql = " AND ".join(where_clauses)
    order_sql = _sort_clause(sort)
    offset = (page - 1) * size

    base_from_sql = f"""
        FROM jobs j
        LEFT JOIN job_classifications jc
          ON jc.job_id = j.id
         AND jc.rule_version = :rule_version
        WHERE {where_sql}
    """

    count_sql = text(f"SELECT COUNT(*) {base_from_sql}")
    total = db.execute(count_sql, {**params, "rule_version": settings.rule_version}).scalar_one()

    data_sql = text(
        f"""
        SELECT
          j.id AS job_id,
          j.title,
          j.company_name,
          j.canonical_url AS url,
          COALESCE(jc.employment_type::text, 'unknown') AS employment_type,
          COALESCE(jc.role_type::text, 'unknown') AS role_type,
          COALESCE(jc.new_grad_score, 0) AS new_grad_score,
          j.posted_at,
          j.deadline_at,
          j.is_active
        {base_from_sql}
        ORDER BY {order_sql}
        LIMIT :limit OFFSET :offset
        """
    )

    rows = db.execute(
        data_sql,
        {
            **params,
            "rule_version": settings.rule_version,
            "limit": size,
            "offset": offset,
        },
    ).mappings().all()

    items = [
        {
            "job_id": row["job_id"],
            "title": row["title"],
            "company_name": row["company_name"],
            "url": row["url"],
            "employment_type": row["employment_type"],
            "role_type": row["role_type"],
            "new_grad_score": row["new_grad_score"],
            "posted_at": _to_iso(row["posted_at"]),
            "deadline_at": _to_iso(row["deadline_at"]),
            "is_active": row["is_active"],
        }
        for row in rows
    ]

    return {"items": items, "page": page, "size": size, "total": total}


@router.get("/today")
def list_today_jobs(
    role_type: str = Query(default="backend"),
    is_active: bool = Query(default=True),
    page: int = Query(default=1, ge=1),
    size: int = Query(default=20, ge=1, le=100),
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    now = datetime.now(timezone.utc)
    today_start = datetime.combine(now.date(), time.min, tzinfo=timezone.utc)

    return list_jobs(
        employment_type=None,
        role_type=role_type,
        is_active=is_active,
        q=None,
        posted_from=today_start,
        posted_to=None,
        deadline_before=None,
        sort="posted_at_desc",
        page=page,
        size=size,
        db=db,
    )


@router.get("/{job_id}")
def get_job_detail(job_id: int, db: Session = Depends(get_db)) -> dict[str, Any]:
    settings = get_settings()
    sql = text(
        """
        SELECT
          j.id AS job_id,
          j.title,
          j.company_name,
          j.canonical_url AS url,
          j.description_text,
          j.location_text,
          j.employment_text_raw,
          j.experience_text_raw,
          j.tech_stack_text,
          j.salary_text,
          j.posted_at,
          j.deadline_at,
          j.is_active,
          COALESCE(jc.employment_type::text, 'unknown') AS employment_type,
          COALESCE(jc.role_type::text, 'unknown') AS role_type,
          COALESCE(jc.new_grad_score, 0) AS new_grad_score,
          COALESCE(jc.confidence, 0.5) AS confidence,
          COALESCE(jc.matched_keywords, '[]'::jsonb) AS matched_keywords,
          jc.reasoning,
          jc.rule_version
        FROM jobs j
        LEFT JOIN job_classifications jc
          ON jc.job_id = j.id
         AND jc.rule_version = :rule_version
        WHERE j.id = :job_id
        """
    )
    row = db.execute(sql, {"job_id": job_id, "rule_version": settings.rule_version}).mappings().first()
    if row is None:
        raise HTTPException(status_code=404, detail="Job not found")

    return {
        "job_id": row["job_id"],
        "title": row["title"],
        "company_name": row["company_name"],
        "url": row["url"],
        "description_text": row["description_text"],
        "location_text": row["location_text"],
        "employment_text_raw": row["employment_text_raw"],
        "experience_text_raw": row["experience_text_raw"],
        "tech_stack_text": row["tech_stack_text"],
        "salary_text": row["salary_text"],
        "employment_type": row["employment_type"],
        "role_type": row["role_type"],
        "new_grad_score": row["new_grad_score"],
        "confidence": float(row["confidence"]),
        "matched_keywords": row["matched_keywords"],
        "reasoning": row["reasoning"],
        "rule_version": row["rule_version"] or settings.rule_version,
        "posted_at": _to_iso(row["posted_at"]),
        "deadline_at": _to_iso(row["deadline_at"]),
        "is_active": row["is_active"],
    }
