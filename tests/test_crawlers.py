from __future__ import annotations

import unittest
from unittest.mock import patch

from app.services.crawler.greenhouse import GreenhouseCrawler
from app.services.crawler.registry import get_crawler
from app.services.crawler.remotive import RemotiveCrawler


class CrawlerTest(unittest.TestCase):
    @patch("app.services.crawler.remotive.fetch_json")
    def test_remotive_fetch_jobs(self, mock_fetch_json):
        mock_fetch_json.return_value = {
            "jobs": [
                {
                    "id": 123,
                    "url": "https://remotive.com/remote-jobs/software-dev/backend-engineer-123",
                    "company_name": "Acme",
                    "title": "Backend Engineer",
                    "description": "Python FastAPI",
                    "candidate_required_location": "Korea",
                    "job_type": "full_time",
                    "tags": ["python", "fastapi"],
                    "salary": "$100k",
                    "publication_date": "2026-02-17T00:00:00+00:00",
                }
            ]
        }

        crawler = RemotiveCrawler()
        jobs = crawler.fetch_jobs()

        self.assertEqual(len(jobs), 1)
        self.assertEqual(jobs[0].source_job_id, "123")
        self.assertEqual(jobs[0].company_name, "Acme")
        self.assertIn("python", jobs[0].tech_stack_text or "")

    @patch("app.services.crawler.greenhouse.fetch_json")
    def test_greenhouse_fetch_jobs(self, mock_fetch_json):
        mock_fetch_json.return_value = {
            "jobs": [
                {
                    "id": 77,
                    "absolute_url": "https://boards.greenhouse.io/moloco/jobs/77",
                    "title": "Backend Platform Engineer",
                    "content": "Build services",
                    "updated_at": "2026-02-17T00:00:00Z",
                    "location": {"name": "Seoul"},
                    "departments": [{"name": "Engineering"}],
                    "offices": [{"name": "Korea"}],
                    "metadata": [{"name": "employment_type", "value": "Full-time"}],
                }
            ]
        }

        crawler = GreenhouseCrawler(source_code="moloco_gh", board_token="moloco", company_name="Moloco")
        jobs = crawler.fetch_jobs()

        self.assertEqual(len(jobs), 1)
        self.assertEqual(jobs[0].source_job_id, "77")
        self.assertEqual(jobs[0].company_name, "Moloco")
        self.assertIn("Engineering", jobs[0].tech_stack_text or "")

    def test_registry(self):
        remotive = get_crawler("remotive")
        self.assertIsInstance(remotive, RemotiveCrawler)

        moloco = get_crawler("moloco_gh")
        self.assertIsInstance(moloco, GreenhouseCrawler)

        with self.assertRaises(ValueError):
            get_crawler("unknown_source")


if __name__ == "__main__":
    unittest.main()
