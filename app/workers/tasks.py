from __future__ import annotations

from app.core.config import get_settings
from app.core.db import SessionLocal
from app.services.classifier.rule_engine import classify_jobs
from app.services.crawler.runner import run_crawl


def crawl_and_classify_once(source_code: str = "remotive", classify_limit: int = 300) -> dict[str, object]:
    settings = get_settings()
    db = SessionLocal()
    try:
        crawl_result = run_crawl(db=db, source_code=source_code)
        classify_result = classify_jobs(db=db, rule_version=settings.rule_version, limit=classify_limit)
        return {"crawl": crawl_result, "classify": classify_result}
    finally:
        db.close()
