from __future__ import annotations

import threading
import uuid
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Callable


@dataclass
class Event:
    type: str = ""
    data: dict[str, Any] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.now)


class EventBus:
    def __init__(self) -> None:
        self._subscribers: dict[str, dict[str, Callable]] = {}
        self._lock = threading.Lock()

    def subscribe(self, event_type: str, callback: Callable[[Event], None]) -> str:
        token = uuid.uuid4().hex
        with self._lock:
            if event_type not in self._subscribers:
                self._subscribers[event_type] = {}
            self._subscribers[event_type][token] = callback
        return token

    def unsubscribe(self, token: str) -> None:
        with self._lock:
            for event_type in self._subscribers:
                self._subscribers[event_type].pop(token, None)

    def publish(self, event: Event) -> None:
        with self._lock:
            handlers = list(self._subscribers.get(event.type, {}).values())
        for handler in handlers:
            try:
                handler(event)
            except Exception:
                pass
