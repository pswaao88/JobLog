from __future__ import annotations

from app.services.crawler.base import BaseCrawler
from app.services.crawler.greenhouse import GreenhouseCrawler
from app.services.crawler.remotive import RemotiveCrawler


def get_crawler(source_code: str) -> BaseCrawler:
    source_code = source_code.strip().lower()
    if source_code == "remotive":
        return RemotiveCrawler()

    if source_code == "moloco_gh":
        return GreenhouseCrawler(source_code="moloco_gh", board_token="moloco", company_name="Moloco")

    if source_code == "sendbird_gh":
        return GreenhouseCrawler(source_code="sendbird_gh", board_token="sendbird", company_name="Sendbird")

    if source_code == "dunamu_gh":
        return GreenhouseCrawler(source_code="dunamu_gh", board_token="dunamu", company_name="Dunamu")

    raise ValueError(f"Unsupported source_code: {source_code}")
