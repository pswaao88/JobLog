from __future__ import annotations

from pathlib import Path

import psycopg

from app.core.config import get_settings


def run_seed() -> None:
    settings = get_settings()
    root = Path(__file__).resolve().parent
    files = [root / "sources_seed.sql", root / "classification_rules_v1.sql"]

    dsn = settings.database_url.replace("+psycopg", "")
    with psycopg.connect(dsn) as conn:
        with conn.cursor() as cur:
            for file in files:
                cur.execute(file.read_text(encoding="utf-8"))
        conn.commit()


if __name__ == "__main__":
    run_seed()
