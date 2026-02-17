from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from sqlalchemy import text
from sqlalchemy.orm import Session

from app.services.crawler.remotive import RemotiveCrawler


def run_crawl(db: Session, source_code: str = "remotive") -> dict[str, Any]:
    source_row = db.execute(
        text("SELECT id, code FROM sources WHERE code = :code AND is_active = true"),
        {"code": source_code},
    ).mappings().first()
    if source_row is None:
        raise ValueError(f"Active source not found: {source_code}")

    run_id = db.execute(
        text(
            """
            INSERT INTO crawl_runs (source_id, status, started_at)
            VALUES (:source_id, 'running', NOW())
            RETURNING id
            """
        ),
        {"source_id": source_row["id"]},
    ).scalar_one()
    db.commit()

    fetched_count = 0
    inserted_count = 0
    updated_count = 0
    failed_count = 0
    error_message: str | None = None

    crawler = RemotiveCrawler()

    try:
        jobs = crawler.fetch_jobs()
        fetched_count = len(jobs)

        for job in jobs:
            existing = db.execute(
                text(
                    """
                    SELECT id
                    FROM jobs
                    WHERE source_id = :source_id
                      AND source_job_id = :source_job_id
                    """
                ),
                {"source_id": source_row["id"], "source_job_id": job.source_job_id},
            ).mappings().first()

            if existing is None:
                db.execute(
                    text(
                        """
                        INSERT INTO jobs (
                            source_id, source_job_id, canonical_url, company_name, title,
                            description_text, location_text, employment_text_raw,
                            experience_text_raw, tech_stack_text, salary_text,
                            posted_at, deadline_at, is_active,
                            first_seen_at, last_seen_at, created_at, updated_at
                        ) VALUES (
                            :source_id, :source_job_id, :canonical_url, :company_name, :title,
                            :description_text, :location_text, :employment_text_raw,
                            :experience_text_raw, :tech_stack_text, :salary_text,
                            :posted_at, :deadline_at, true,
                            NOW(), NOW(), NOW(), NOW()
                        )
                        """
                    ),
                    {
                        "source_id": source_row["id"],
                        "source_job_id": job.source_job_id,
                        "canonical_url": job.canonical_url,
                        "company_name": job.company_name,
                        "title": job.title,
                        "description_text": job.description_text,
                        "location_text": job.location_text,
                        "employment_text_raw": job.employment_text_raw,
                        "experience_text_raw": job.experience_text_raw,
                        "tech_stack_text": job.tech_stack_text,
                        "salary_text": job.salary_text,
                        "posted_at": job.posted_at,
                        "deadline_at": job.deadline_at,
                    },
                )
                inserted_count += 1
            else:
                db.execute(
                    text(
                        """
                        UPDATE jobs
                        SET canonical_url = :canonical_url,
                            company_name = :company_name,
                            title = :title,
                            description_text = :description_text,
                            location_text = :location_text,
                            employment_text_raw = :employment_text_raw,
                            experience_text_raw = :experience_text_raw,
                            tech_stack_text = :tech_stack_text,
                            salary_text = :salary_text,
                            posted_at = :posted_at,
                            deadline_at = :deadline_at,
                            is_active = true,
                            last_seen_at = NOW(),
                            updated_at = NOW()
                        WHERE id = :job_id
                        """
                    ),
                    {
                        "job_id": existing["id"],
                        "canonical_url": job.canonical_url,
                        "company_name": job.company_name,
                        "title": job.title,
                        "description_text": job.description_text,
                        "location_text": job.location_text,
                        "employment_text_raw": job.employment_text_raw,
                        "experience_text_raw": job.experience_text_raw,
                        "tech_stack_text": job.tech_stack_text,
                        "salary_text": job.salary_text,
                        "posted_at": job.posted_at,
                        "deadline_at": job.deadline_at,
                    },
                )
                updated_count += 1

        status = "success"
    except Exception as exc:
        status = "failed"
        failed_count = 1
        error_message = str(exc)

    db.execute(
        text(
            """
            UPDATE crawl_runs
            SET finished_at = :finished_at,
                status = :status,
                fetched_count = :fetched_count,
                inserted_count = :inserted_count,
                updated_count = :updated_count,
                failed_count = :failed_count,
                error_message = :error_message
            WHERE id = :run_id
            """
        ),
        {
            "finished_at": datetime.now(timezone.utc),
            "status": status,
            "fetched_count": fetched_count,
            "inserted_count": inserted_count,
            "updated_count": updated_count,
            "failed_count": failed_count,
            "error_message": error_message,
            "run_id": run_id,
        },
    )
    db.commit()

    if status == "failed":
        raise RuntimeError(error_message or "crawl failed")

    return {
        "run_id": run_id,
        "status": status,
        "source_code": source_code,
        "fetched_count": fetched_count,
        "inserted_count": inserted_count,
        "updated_count": updated_count,
    }
