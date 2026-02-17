from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime


@dataclass
class CrawlJob:
    source_job_id: str
    canonical_url: str
    company_name: str
    title: str
    description_text: str | None = None
    location_text: str | None = None
    employment_text_raw: str | None = None
    experience_text_raw: str | None = None
    tech_stack_text: str | None = None
    salary_text: str | None = None
    posted_at: datetime | None = None
    deadline_at: datetime | None = None


class BaseCrawler:
    source_code: str

    def fetch_jobs(self) -> list[CrawlJob]:
        raise NotImplementedError
