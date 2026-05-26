"""QMT connection client with auto-reconnect."""
from __future__ import annotations

import threading
import time

from loguru import logger


class QmtClient:
    """xtquant xttrader connection manager."""

    def __init__(self, qmt_path: str, account_id: str, account_type: str = "STOCK") -> None:
        self._qmt_path = qmt_path
        self._account_id = account_id
        self._account_type = account_type
        self._connected = False
        self._trader = None
        self._lock = threading.Lock()

    def connect(self) -> bool:
        with self._lock:
            try:
                from xtquant import xttrader
                self._trader = xttrader.XtQuantTrader(self._qmt_path, session_id=1)
                self._trader.start()
                result = self._trader.connect()
                if result == 0:
                    self._connected = True
                    logger.info("QMT connected")
                    return True
                logger.error(f"QMT connect failed: {result}")
                return False
            except Exception as e:
                logger.error(f"QMT connect error: {e}")
                self._connected = False
                return False

    def disconnect(self) -> None:
        with self._lock:
            if self._trader:
                self._trader.stop()
            self._connected = False

    def is_connected(self) -> bool:
        return self._connected

    def reconnect(self, max_retries: int = 5) -> bool:
        for attempt in range(max_retries):
            logger.info(f"Reconnecting... attempt {attempt + 1}/{max_retries}")
            if self.connect():
                return True
            wait = min(2 ** attempt, 30)
            time.sleep(wait)
        logger.error("Reconnect failed after max retries")
        return False

    @property
    def trader(self):
        return self._trader

    @property
    def account_id(self) -> str:
        return self._account_id

    @property
    def account_type(self) -> str:
        return self._account_type
