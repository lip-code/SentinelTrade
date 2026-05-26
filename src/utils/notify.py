"""Notification interface for alerts and risk events."""
from __future__ import annotations

from abc import ABC, abstractmethod

from loguru import logger


class Notifier(ABC):
    @abstractmethod
    def send(self, title: str, message: str) -> bool: ...


class LogNotifier(Notifier):
    """Logs notifications via loguru."""

    def send(self, title: str, message: str) -> bool:
        logger.warning(f"[NOTIFY] {title}: {message}")
        return True


class NoopNotifier(Notifier):
    """Silent notifier for testing or when notifications are disabled."""

    def send(self, title: str, message: str) -> bool:
        return True


def create_notifier(notify_type: str = "none") -> Notifier:
    if notify_type == "log":
        return LogNotifier()
    return NoopNotifier()
