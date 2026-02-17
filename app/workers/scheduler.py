from __future__ import annotations

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger

from app.workers.tasks import crawl_and_classify_once

scheduler = BackgroundScheduler(timezone="Asia/Seoul")


def start_scheduler() -> None:
    if scheduler.running:
        return

    # MVP: 하루 2회 실행 (09:00, 18:00 KST)
    scheduler.add_job(
        crawl_and_classify_once,
        trigger=CronTrigger(hour="9,18", minute=0),
        id="crawl_and_classify_job",
        replace_existing=True,
        max_instances=1,
        coalesce=True,
    )
    scheduler.start()


def stop_scheduler() -> None:
    if scheduler.running:
        scheduler.shutdown(wait=False)
