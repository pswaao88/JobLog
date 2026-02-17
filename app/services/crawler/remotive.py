from __future__ import annotations

from datetime import datetime
from urllib.parse import urlparse

from app.services.crawler.base import BaseCrawler, CrawlJob
from app.services.crawler.http_client import fetch_json


class RemotiveCrawler(BaseCrawler):
    source_code = "remotive"
    endpoint = "https://remotive.com/api/remote-jobs?search=backend"

    def fetch_jobs(self) -> list[CrawlJob]:
        payload = fetch_json(self.endpoint)

        jobs: list[CrawlJob] = []
        for item in payload.get("jobs", []):
            url = item.get("url")
            if not url:
                continue

            source_job_id = str(item.get("id") or urlparse(url).path)
            posted_raw = item.get("publication_date")
            posted_at = self._parse_datetime(posted_raw)

            jobs.append(
                CrawlJob(
                    source_job_id=source_job_id,
                    canonical_url=url,
                    company_name=item.get("company_name") or "Unknown",
                    title=item.get("title") or "Untitled",
                    description_text=item.get("description"),
                    location_text=item.get("candidate_required_location"),
                    employment_text_raw=item.get("job_type"),
                    experience_text_raw=None,
                    tech_stack_text=", ".join(item.get("tags") or []),
                    salary_text=item.get("salary"),
                    posted_at=posted_at,
                    deadline_at=None,
                )
            )

        return jobs

    @staticmethod
    def _parse_datetime(value: str | None) -> datetime | None:
        if not value:
            return None
        cleaned = value.replace("Z", "+00:00")
        try:
            return datetime.fromisoformat(cleaned)
        except ValueError:
            return None
