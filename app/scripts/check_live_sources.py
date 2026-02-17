from __future__ import annotations

from app.services.crawler.registry import get_crawler

SOURCES = ["remotive", "moloco_gh", "sendbird_gh", "dunamu_gh"]


def main() -> None:
    for code in SOURCES:
        crawler = get_crawler(code)
        try:
            jobs = crawler.fetch_jobs()
            print(f"{code}: ok ({len(jobs)} jobs)")
            if jobs:
                sample = jobs[0]
                print(f"  sample: {sample.company_name} | {sample.title}")
        except Exception as exc:
            print(f"{code}: fail ({exc})")


if __name__ == "__main__":
    main()
