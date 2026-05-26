"""APScheduler wrapper for daily and interval tasks."""
from __future__ import annotations

from typing import Callable

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from loguru import logger


class TaskScheduler:
    """Manages scheduled trading tasks."""

    def __init__(self) -> None:
        self._scheduler = BackgroundScheduler()
        self._started = False

    def add_daily_task(self, time_str: str, func: Callable, name: str) -> None:
        hour, minute = time_str.split(":")
        self._scheduler.add_job(
            func,
            trigger=CronTrigger(hour=int(hour), minute=int(minute), day_of_week="mon-fri"),
            id=name,
            name=name,
            replace_existing=True,
        )
        logger.info(f"Scheduled daily task '{name}' at {time_str}")

    def add_interval_task(self, seconds: int, func: Callable, name: str) -> None:
        self._scheduler.add_job(
            func,
            trigger="interval",
            seconds=seconds,
            id=name,
            name=name,
            replace_existing=True,
        )
        logger.info(f"Scheduled interval task '{name}' every {seconds}s")

    def start(self) -> None:
        if not self._started:
            self._scheduler.start()
            self._started = True
            logger.info("Scheduler started")

    def stop(self) -> None:
        if self._started:
            self._scheduler.shutdown()
            self._started = False
            logger.info("Scheduler stopped")

    def get_jobs(self) -> list:
        return self._scheduler.get_jobs()
