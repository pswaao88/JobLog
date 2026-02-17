from __future__ import annotations

import json
import time
from typing import Any
from urllib.request import Request, urlopen

DEFAULT_HEADERS = {
    "User-Agent": "JobLogCrawler/1.0 (+https://joblog.local)",
    "Accept": "application/json,text/plain,*/*",
}


def fetch_json(url: str, timeout: int = 15, retries: int = 2) -> dict[str, Any]:
    last_error: Exception | None = None
    for attempt in range(retries + 1):
        try:
            req = Request(url, headers=DEFAULT_HEADERS)
            with urlopen(req, timeout=timeout) as response:
                payload = response.read().decode("utf-8")
            return json.loads(payload)
        except Exception as exc:  # network/domain dependent
            last_error = exc
            if attempt < retries:
                time.sleep(0.5 * (attempt + 1))

    raise RuntimeError(f"failed to fetch json from {url}: {last_error}")
