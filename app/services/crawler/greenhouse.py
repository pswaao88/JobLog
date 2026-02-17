from __future__ import annotations

from datetime import datetime

from app.services.crawler.base import BaseCrawler, CrawlJob
from app.services.crawler.http_client import fetch_json


class GreenhouseCrawler(BaseCrawler):
    def __init__(self, source_code: str, board_token: str, company_name: str):
        self.source_code = source_code
        self.board_token = board_token
        self.company_name = company_name
        self.endpoint = f"https://boards-api.greenhouse.io/v1/boards/{board_token}/jobs?content=true"

    def fetch_jobs(self) -> list[CrawlJob]:
        payload = fetch_json(self.endpoint)

        jobs: list[CrawlJob] = []
        for item in payload.get("jobs", []):
            job_id = str(item.get("id") or "")
            absolute_url = item.get("absolute_url")
            title = item.get("title")
            if not job_id or not absolute_url or not title:
                continue

            location_obj = item.get("location") or {}
            metadata = item.get("metadata") or []
            dept = item.get("departments") or []
            offices = item.get("offices") or []
            content = item.get("content") or ""

            posted_at = self._parse_datetime(item.get("updated_at"))

            tags = []
            if dept:
                tags.extend([d.get("name") for d in dept if d.get("name")])
            if offices:
                tags.extend([o.get("name") for o in offices if o.get("name")])
            for meta in metadata:
                meta_name = meta.get("name")
                meta_value = meta.get("value")
                if meta_name and meta_value:
                    tags.append(f"{meta_name}:{meta_value}")

            jobs.append(
                CrawlJob(
                    source_job_id=job_id,
                    canonical_url=absolute_url,
                    company_name=self.company_name,
                    title=title,
                    description_text=content,
                    location_text=location_obj.get("name"),
                    employment_text_raw=None,
                    experience_text_raw=None,
                    tech_stack_text=", ".join(tags) if tags else None,
                    salary_text=None,
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
