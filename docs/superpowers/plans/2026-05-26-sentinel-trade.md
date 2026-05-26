# SentinelTrade ETF 自动交易系统 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a complete A-share ETF automated trading system with event-driven architecture, trend rotation strategy, comprehensive risk control, and web dashboard.

**Architecture:** Event-driven with EventBus decoupling modules. Each module has an abstract base class and concrete implementation. Config-driven via YAML + .env. SQLite for persistence, APScheduler for task scheduling, Streamlit for dashboard.

**Tech Stack:** Python 3.11, xtquant, SQLite, APScheduler, Streamlit, loguru, pandas, numpy, plotly

---

## File Map

### Foundation (Tasks 1-3)
- `requirements.txt` - Dependencies
- `config.yaml` - Runtime config
- `.env` - Secrets template
- `src/config/settings.py` - Config dataclasses
- `src/config/loader.py` - YAML/ENV loader
- `src/common/enums.py` - Shared enumerations
- `src/common/types.py` - Shared dataclasses
- `src/common/events.py` - EventBus
- `src/utils/logger.py` - loguru setup
- `src/utils/notify.py` - Notification interface
- `src/utils/trading_calendar.py` - Trading calendar

### Data Layer (Task 4)
- `src/database/engine.py` - SQLite connection
- `src/database/models.py` - Table definitions
- `src/database/repository.py` - CRUD operations

### Market (Task 5)
- `src/market/market_base.py` - Abstract market provider
- `src/market/xt_provider.py` - xtquant implementation
- `src/market/data_cache.py` - Quote cache

### Strategy (Task 6)
- `src/strategy/strategy_base.py` - Abstract strategy
- `src/strategy/signal.py` - Signal dataclass
- `src/strategy/factor.py` - Factor calculations
- `src/strategy/etf_rotation.py` - ETF rotation strategy
- `src/strategy/strategy_manager.py` - Strategy orchestrator

### Risk (Task 7)
- `src/risk/risk_base.py` - Abstract risk rule
- `src/risk/risk_engine.py` - Rule chain engine
- `src/risk/stop_loss.py` - Stop loss/profit rules
- `src/risk/position_limit.py` - Position limits
- `src/risk/breaker.py` - Circuit breaker
- `src/risk/blacklist.py` - Blacklist & anomaly detection

### Broker (Task 8)
- `src/broker/broker_base.py` - Abstract broker
- `src/broker/qmt_client.py` - QMT connection
- `src/broker/order_manager.py` - Order management
- `src/broker/trade_callback.py` - Trade callbacks
- `src/broker/account_manager.py` - Account queries
- `src/broker/paper_broker.py` - Paper trading

### Scheduler (Task 9)
- `src/scheduler/task_scheduler.py` - APScheduler wrapper

### Backtest (Task 10)
- `src/backtest/engine.py` - Backtest engine
- `src/backtest/data_loader.py` - Historical data loader
- `src/backtest/report.py` - Backtest reporting

### Dashboard (Task 11)
- `src/dashboard/app.py` - Streamlit main
- `src/dashboard/pages/portfolio.py` - Portfolio page
- `src/dashboard/pages/signals.py` - Signals page
- `src/dashboard/pages/trades.py` - Trades page
- `src/dashboard/pages/risk.py` - Risk status page
- `src/dashboard/components/charts.py` - Chart components
- `src/dashboard/components/metrics.py` - Metric cards

### AI Placeholder (Task 12)
- `src/ai/ai_base.py` - Abstract AI model
- `src/ai/feature_engine.py` - Feature engineering

### Integration (Task 13)
- `main.py` - Application entry point
- `README.md` - Documentation

---

## Task 1: Project Scaffolding

**Files:**
- Create: `requirements.txt`, `config.yaml`, `.env`, `README.md`
- Create: `src/__init__.py`, all module `__init__.py` files
- Create: `data/`, `data/logs/`

- [ ] **Step 1: Create directory structure**

```bash
mkdir -p src/config src/common src/database src/market src/strategy src/risk src/broker src/scheduler src/dashboard/pages src/dashboard/components src/backtest src/ai src/utils data/logs tests
```

- [ ] **Step 2: Create requirements.txt**

```
xtquant>=1.0.0
pandas>=2.0.0
numpy>=1.24.0
pyyaml>=6.0
python-dotenv>=1.0.0
apscheduler>=3.10.0
streamlit>=1.28.0
plotly>=5.18.0
loguru>=0.7.0
typing-extensions>=4.8.0
pytest>=7.4.0
```

- [ ] **Step 3: Create .env template**

```
QMT_PATH=C:\国金证券QMT交易端\userdata_mini
QMT_ACCOUNT=your_account_id
QMT_ACCOUNT_TYPE=STOCK
DB_PATH=data/sentinel.db
NOTIFY_TYPE=none
WECHAT_WEBHOOK=
DINGTALK_WEBHOOK=
```

- [ ] **Step 4: Create config.yaml**

```yaml
etf_pool:
  - { code: "510300", name: "沪深300ETF" }
  - { code: "510500", name: "中证500ETF" }
  - { code: "159915", name: "创业板ETF" }
  - { code: "512100", name: "中证1000ETF" }
  - { code: "159941", name: "纳指ETF" }
  - { code: "518880", name: "黄金ETF" }
  - { code: "511010", name: "国债ETF" }

strategy:
  ma_periods: [5, 10, 20]
  trend_threshold: 0.02
  max_holdings: 3
  rebalance_days: [0, 4]

risk:
  max_position_ratio: 0.30
  max_drawdown: 0.05
  daily_loss_limit: 0.02
  stop_profit: 0.08
  stop_loss: 0.03
  max_consecutive_losses: 3
  cooldown_minutes: 30

scheduler:
  scan_time: "09:35"
  rebalance_time: "14:30"
  close_check_time: "14:50"
  settle_time: "15:05"

database:
  path: "data/sentinel.db"

logging:
  level: "DEBUG"
  rotation: "1 day"
  retention: "30 days"
```

- [ ] **Step 5: Create all __init__.py files (empty)**

Create empty `__init__.py` in: `src/`, `src/config/`, `src/common/`, `src/database/`, `src/market/`, `src/strategy/`, `src/risk/`, `src/broker/`, `src/scheduler/`, `src/dashboard/`, `src/backtest/`, `src/ai/`, `src/utils/`

- [ ] **Step 6: Commit**

```bash
git add requirements.txt config.yaml .env src/__init__.py data/
git commit -m "feat: project scaffolding with config and directory structure"
```

---

## Task 2: Config Module

**Files:**
- Create: `src/config/settings.py`
- Create: `src/config/loader.py`
- Create: `tests/test_config.py`

- [ ] **Step 1: Write test for config loading**

```python
# tests/test_config.py
import pytest
import yaml
import tempfile
import os
from pathlib import Path
from src.config.settings import AppConfig, StrategyConfig, RiskConfig
from src.config.loader import load_config


def test_load_config_from_yaml(tmp_path):
    config_data = {
        "etf_pool": [{"code": "510300", "name": "沪深300ETF"}],
        "strategy": {
            "ma_periods": [5, 10, 20],
            "trend_threshold": 0.02,
            "max_holdings": 3,
            "rebalance_days": [0, 4],
        },
        "risk": {
            "max_position_ratio": 0.30,
            "max_drawdown": 0.05,
            "daily_loss_limit": 0.02,
            "stop_profit": 0.08,
            "stop_loss": 0.03,
            "max_consecutive_losses": 3,
            "cooldown_minutes": 30,
        },
        "scheduler": {
            "scan_time": "09:35",
            "rebalance_time": "14:30",
            "close_check_time": "14:50",
            "settle_time": "15:05",
        },
        "database": {"path": "data/sentinel.db"},
        "logging": {"level": "DEBUG", "rotation": "1 day", "retention": "30 days"},
    }
    config_file = tmp_path / "config.yaml"
    config_file.write_text(yaml.dump(config_data))

    config = load_config(str(config_file))

    assert isinstance(config, AppConfig)
    assert config.strategy.max_holdings == 3
    assert config.risk.stop_loss == 0.03
    assert len(config.etf_pool) == 1
    assert config.etf_pool[0].code == "510300"


def test_config_defaults():
    config = AppConfig()
    assert config.strategy.max_holdings == 3
    assert config.risk.stop_loss == 0.03
```

- [ ] **Step 2: Run test to verify it fails**

```bash
pytest tests/test_config.py -v
```
Expected: FAIL with ModuleNotFoundError

- [ ] **Step 3: Implement settings.py**

```python
# src/config/settings.py
from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class EtfItem:
    code: str = ""
    name: str = ""


@dataclass
class StrategyConfig:
    ma_periods: list[int] = field(default_factory=lambda: [5, 10, 20])
    trend_threshold: float = 0.02
    max_holdings: int = 3
    rebalance_days: list[int] = field(default_factory=lambda: [0, 4])


@dataclass
class RiskConfig:
    max_position_ratio: float = 0.30
    max_drawdown: float = 0.05
    daily_loss_limit: float = 0.02
    stop_profit: float = 0.08
    stop_loss: float = 0.03
    max_consecutive_losses: int = 3
    cooldown_minutes: int = 30


@dataclass
class SchedulerConfig:
    scan_time: str = "09:35"
    rebalance_time: str = "14:30"
    close_check_time: str = "14:50"
    settle_time: str = "15:05"


@dataclass
class DatabaseConfig:
    path: str = "data/sentinel.db"


@dataclass
class LoggingConfig:
    level: str = "DEBUG"
    rotation: str = "1 day"
    retention: str = "30 days"


@dataclass
class BrokerConfig:
    qmt_path: str = ""
    qmt_account: str = ""
    qmt_account_type: str = "STOCK"


@dataclass
class AppConfig:
    etf_pool: list[EtfItem] = field(default_factory=list)
    strategy: StrategyConfig = field(default_factory=StrategyConfig)
    risk: RiskConfig = field(default_factory=RiskConfig)
    scheduler: SchedulerConfig = field(default_factory=SchedulerConfig)
    database: DatabaseConfig = field(default_factory=DatabaseConfig)
    logging: LoggingConfig = field(default_factory=LoggingConfig)
    broker: BrokerConfig = field(default_factory=BrokerConfig)
```

- [ ] **Step 4: Implement loader.py**

```python
# src/config/loader.py
from __future__ import annotations

import os
from pathlib import Path

import yaml
from dotenv import load_dotenv

from src.config.settings import (
    AppConfig,
    BrokerConfig,
    DatabaseConfig,
    EtfItem,
    LoggingConfig,
    RiskConfig,
    SchedulerConfig,
    StrategyConfig,
)


def load_config(config_path: str = "config.yaml") -> AppConfig:
    load_dotenv()

    with open(config_path, "r", encoding="utf-8") as f:
        raw: dict = yaml.safe_load(f) or {}

    etf_pool = [EtfItem(**item) for item in raw.get("etf_pool", [])]

    strategy_raw = raw.get("strategy", {})
    strategy = StrategyConfig(**strategy_raw) if strategy_raw else StrategyConfig()

    risk_raw = raw.get("risk", {})
    risk = RiskConfig(**risk_raw) if risk_raw else RiskConfig()

    scheduler_raw = raw.get("scheduler", {})
    scheduler = SchedulerConfig(**scheduler_raw) if scheduler_raw else SchedulerConfig()

    db_raw = raw.get("database", {})
    db_path = os.getenv("DB_PATH", db_raw.get("path", "data/sentinel.db"))
    database = DatabaseConfig(path=db_path)

    log_raw = raw.get("logging", {})
    logging_cfg = LoggingConfig(**log_raw) if log_raw else LoggingConfig()

    broker = BrokerConfig(
        qmt_path=os.getenv("QMT_PATH", ""),
        qmt_account=os.getenv("QMT_ACCOUNT", ""),
        qmt_account_type=os.getenv("QMT_ACCOUNT_TYPE", "STOCK"),
    )

    return AppConfig(
        etf_pool=etf_pool,
        strategy=strategy,
        risk=risk,
        scheduler=scheduler,
        database=database,
        logging=logging_cfg,
        broker=broker,
    )
```

- [ ] **Step 5: Run test to verify it passes**

```bash
pytest tests/test_config.py -v
```
Expected: PASS

- [ ] **Step 6: Commit**

```bash
git add src/config/ tests/test_config.py
git commit -m "feat: config module with dataclass settings and YAML loader"
```

---

## Task 3: Common Module (types, enums, events)

**Files:**
- Create: `src/common/enums.py`
- Create: `src/common/types.py`
- Create: `src/common/events.py`
- Create: `tests/test_events.py`

- [ ] **Step 1: Write test for EventBus**

```python
# tests/test_events.py
import pytest
from src.common.events import EventBus, Event


def test_event_bus_publish_subscribe():
    bus = EventBus()
    received = []

    def handler(event: Event):
        received.append(event)

    bus.subscribe("test_event", handler)
    bus.publish(Event(type="test_event", data={"key": "value"}))

    assert len(received) == 1
    assert received[0].type == "test_event"
    assert received[0].data["key"] == "value"


def test_event_bus_multiple_subscribers():
    bus = EventBus()
    count = {"a": 0, "b": 0}

    bus.subscribe("test", lambda e: count.__setitem__("a", count["a"] + 1))
    bus.subscribe("test", lambda e: count.__setitem__("b", count["b"] + 1))
    bus.publish(Event(type="test", data={}))

    assert count["a"] == 1
    assert count["b"] == 1


def test_event_bus_no_subscribers():
    bus = EventBus()
    bus.publish(Event(type="unknown", data={}))  # Should not raise


def test_event_bus_unsubscribe():
    bus = EventBus()
    count = [0]

    def handler(event):
        count[0] += 1

    token = bus.subscribe("test", handler)
    bus.publish(Event(type="test", data={}))
    assert count[0] == 1

    bus.unsubscribe(token)
    bus.publish(Event(type="test", data={}))
    assert count[0] == 1
```

- [ ] **Step 2: Run test to verify it fails**

```bash
pytest tests/test_events.py -v
```
Expected: FAIL with ModuleNotFoundError

- [ ] **Step 3: Implement enums.py**

```python
# src/common/enums.py
from enum import Enum, auto


class Direction(Enum):
    BUY = "buy"
    SELL = "sell"


class OrderStatus(Enum):
    PENDING = "pending"
    FILLED = "filled"
    PARTIAL = "partial"
    CANCELLED = "cancelled"
    REJECTED = "rejected"


class SignalType(Enum):
    ENTRY = "entry"
    EXIT = "exit"
    STOP_LOSS = "stop_loss"
    STOP_PROFIT = "stop_profit"


class TrendDirection(Enum):
    UP = "up"
    DOWN = "down"
    SIDEWAYS = "sideways"
```

- [ ] **Step 4: Implement types.py**

```python
# src/common/types.py
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime

from src.common.enums import Direction, OrderStatus, SignalType


@dataclass
class Bar:
    code: str = ""
    open: float = 0.0
    high: float = 0.0
    low: float = 0.0
    close: float = 0.0
    volume: float = 0.0
    timestamp: datetime = field(default_factory=datetime.now)


@dataclass
class Tick:
    code: str = ""
    last_price: float = 0.0
    bid_price: float = 0.0
    ask_price: float = 0.0
    volume: float = 0.0
    timestamp: datetime = field(default_factory=datetime.now)


@dataclass
class Signal:
    code: str = ""
    direction: Direction = Direction.BUY
    signal_type: SignalType = SignalType.ENTRY
    strength: float = 0.0
    price: float = 0.0
    source: str = ""
    timestamp: datetime = field(default_factory=datetime.now)


@dataclass
class Order:
    order_id: str = ""
    code: str = ""
    direction: Direction = Direction.BUY
    price: float = 0.0
    volume: int = 0
    status: OrderStatus = OrderStatus.PENDING
    filled_volume: int = 0
    filled_price: float = 0.0
    timestamp: datetime = field(default_factory=datetime.now)


@dataclass
class Trade:
    trade_id: str = ""
    order_id: str = ""
    code: str = ""
    direction: Direction = Direction.BUY
    price: float = 0.0
    volume: int = 0
    commission: float = 0.0
    timestamp: datetime = field(default_factory=datetime.now)


@dataclass
class Position:
    code: str = ""
    name: str = ""
    volume: int = 0
    available: int = 0
    cost_price: float = 0.0
    current_price: float = 0.0
    market_value: float = 0.0
    pnl: float = 0.0
    pnl_ratio: float = 0.0


@dataclass
class Account:
    total_assets: float = 0.0
    balance: float = 0.0
    available: float = 0.0
    frozen: float = 0.0
    market_value: float = 0.0
    daily_pnl: float = 0.0
```

- [ ] **Step 5: Implement events.py**

```python
# src/common/events.py
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
                pass  # Swallow handler errors to not break other handlers
```

- [ ] **Step 6: Run test to verify it passes**

```bash
pytest tests/test_events.py -v
```
Expected: PASS

- [ ] **Step 7: Commit**

```bash
git add src/common/ tests/test_events.py
git commit -m "feat: common module with types, enums, and EventBus"
```

---

## Task 4: Utils Module (logger, trading calendar, notify)

**Files:**
- Create: `src/utils/logger.py`
- Create: `src/utils/trading_calendar.py`
- Create: `src/utils/notify.py`
- Create: `tests/test_trading_calendar.py`

- [ ] **Step 1: Write test for trading calendar**

```python
# tests/test_trading_calendar.py
import pytest
from datetime import date
from src.utils.trading_calendar import TradingCalendar


def test_is_trading_day_weekday():
    cal = TradingCalendar()
    # 2026-05-25 is a Monday
    assert cal.is_trading_day(date(2026, 5, 25)) is True


def test_is_not_trading_day_weekend():
    cal = TradingCalendar()
    # 2026-05-23 is a Saturday
    assert cal.is_trading_day(date(2026, 5, 23)) is False


def test_next_trading_day():
    cal = TradingCalendar()
    # Friday -> next Monday
    result = cal.next_trading_day(date(2026, 5, 22))
    assert result == date(2026, 5, 25)
```

- [ ] **Step 2: Run test to verify it fails**

```bash
pytest tests/test_trading_calendar.py -v
```
Expected: FAIL

- [ ] **Step 3: Implement logger.py**

```python
# src/utils/logger.py
import sys
from pathlib import Path

from loguru import logger


def setup_logger(
    level: str = "DEBUG",
    rotation: str = "1 day",
    retention: str = "30 days",
    log_dir: str = "data/logs",
) -> None:
    logger.remove()

    log_path = Path(log_dir)
    log_path.mkdir(parents=True, exist_ok=True)

    logger.add(
        sys.stdout,
        level=level,
        format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan> | <level>{message}</level>",
        colorize=True,
    )

    logger.add(
        str(log_path / "sentinel_{time:YYYY-MM-DD}.log"),
        level="DEBUG",
        format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} | {message}",
        rotation=rotation,
        retention=retention,
        encoding="utf-8",
    )

    logger.add(
        str(log_path / "error_{time:YYYY-MM-DD}.log"),
        level="ERROR",
        format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} | {message}",
        rotation=rotation,
        retention=retention,
        encoding="utf-8",
    )

    logger.add(
        str(log_path / "risk_{time:YYYY-MM-DD}.log"),
        level="INFO",
        format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {message}",
        rotation=rotation,
        retention=retention,
        encoding="utf-8",
        filter=lambda record: "risk" in record["extra"].get("module", ""),
    )
```

- [ ] **Step 4: Implement trading_calendar.py**

```python
# src/utils/trading_calendar.py
from __future__ import annotations

from datetime import date, timedelta


class TradingCalendar:
    def __init__(self, holidays: list[date] | None = None) -> None:
        self._holidays: set[date] = set(holidays or [])

    def is_trading_day(self, d: date) -> bool:
        if d.weekday() >= 5:
            return False
        return d not in self._holidays

    def next_trading_day(self, d: date) -> date:
        next_day = d + timedelta(days=1)
        while not self.is_trading_day(next_day):
            next_day += timedelta(days=1)
        return next_day

    def prev_trading_day(self, d: date) -> date:
        prev_day = d - timedelta(days=1)
        while not self.is_trading_day(prev_day):
            prev_day -= timedelta(days=1)
        return prev_day
```

- [ ] **Step 5: Implement notify.py**

```python
# src/utils/notify.py
from __future__ import annotations

from abc import ABC, abstractmethod

from loguru import logger


class Notifier(ABC):
    @abstractmethod
    def send(self, title: str, message: str) -> bool: ...


class LogNotifier(Notifier):
    def send(self, title: str, message: str) -> bool:
        logger.warning(f"[NOTIFY] {title}: {message}")
        return True


class NoopNotifier(Notifier):
    def send(self, title: str, message: str) -> bool:
        return True


def create_notifier(notify_type: str = "none") -> Notifier:
    if notify_type == "log":
        return LogNotifier()
    return NoopNotifier()
```

- [ ] **Step 6: Run test to verify it passes**

```bash
pytest tests/test_trading_calendar.py -v
```
Expected: PASS

- [ ] **Step 7: Commit**

```bash
git add src/utils/ tests/test_trading_calendar.py
git commit -m "feat: utils module with logger, trading calendar, and notifier"
```

---

## Task 5: Database Module

**Files:**
- Create: `src/database/engine.py`
- Create: `src/database/models.py`
- Create: `src/database/repository.py`
- Create: `tests/test_database.py`

- [ ] **Step 1: Write test for database**

```python
# tests/test_database.py
import pytest
from datetime import datetime
from src.database.engine import DatabaseEngine
from src.database.repository import TradeRepository, SignalRepository
from src.common.enums import Direction, OrderStatus, SignalType


@pytest.fixture
def db_engine(tmp_path):
    db_path = str(tmp_path / "test.db")
    engine = DatabaseEngine(db_path)
    engine.init_tables()
    return engine


def test_save_and_query_trade(db_engine):
    repo = TradeRepository(db_engine)
    repo.save_trade(
        code="510300",
        direction=Direction.BUY,
        price=4.5,
        volume=1000,
        commission=1.0,
    )
    trades = repo.get_trades()
    assert len(trades) == 1
    assert trades[0].code == "510300"


def test_save_and_query_signal(db_engine):
    repo = SignalRepository(db_engine)
    repo.save_signal(
        code="510300",
        signal_type=SignalType.ENTRY,
        strength=0.8,
        source="etf_rotation",
    )
    signals = repo.get_signals()
    assert len(signals) == 1
    assert signals[0].strength == 0.8
```

- [ ] **Step 2: Run test to verify it fails**

```bash
pytest tests/test_database.py -v
```
Expected: FAIL

- [ ] **Step 3: Implement engine.py**

```python
# src/database/engine.py
from __future__ import annotations

import sqlite3
from pathlib import Path


class DatabaseEngine:
    def __init__(self, db_path: str = "data/sentinel.db") -> None:
        self._db_path = db_path
        Path(db_path).parent.mkdir(parents=True, exist_ok=True)
        self._conn = sqlite3.connect(db_path, check_same_thread=False)
        self._conn.row_factory = sqlite3.Row

    @property
    def connection(self) -> sqlite3.Connection:
        return self._conn

    def init_tables(self) -> None:
        cursor = self._conn.cursor()
        cursor.executescript("""
            CREATE TABLE IF NOT EXISTS trades (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                code TEXT NOT NULL,
                direction TEXT NOT NULL,
                price REAL NOT NULL,
                volume INTEGER NOT NULL,
                commission REAL DEFAULT 0,
                pnl REAL DEFAULT 0,
                timestamp TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS signals (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                code TEXT NOT NULL,
                signal_type TEXT NOT NULL,
                strength REAL DEFAULT 0,
                price REAL DEFAULT 0,
                source TEXT DEFAULT '',
                timestamp TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS daily_pnl (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                date TEXT NOT NULL UNIQUE,
                total_assets REAL NOT NULL,
                pnl REAL DEFAULT 0,
                drawdown REAL DEFAULT 0
            );
            CREATE TABLE IF NOT EXISTS risk_events (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                event_type TEXT NOT NULL,
                detail TEXT DEFAULT '',
                timestamp TEXT NOT NULL
            );
        """)
        self._conn.commit()

    def close(self) -> None:
        self._conn.close()
```

- [ ] **Step 4: Implement repository.py**

```python
# src/database/repository.py
from __future__ import annotations

from datetime import datetime

from src.common.enums import Direction, SignalType
from src.database.engine import DatabaseEngine


class TradeRepository:
    def __init__(self, engine: DatabaseEngine) -> None:
        self._engine = engine

    def save_trade(
        self,
        code: str,
        direction: Direction,
        price: float,
        volume: int,
        commission: float = 0.0,
        pnl: float = 0.0,
    ) -> int:
        conn = self._engine.connection
        cursor = conn.execute(
            "INSERT INTO trades (code, direction, price, volume, commission, pnl, timestamp) VALUES (?, ?, ?, ?, ?, ?, ?)",
            (code, direction.value, price, volume, commission, pnl, datetime.now().isoformat()),
        )
        conn.commit()
        return cursor.lastrowid

    def get_trades(self, limit: int = 100) -> list[dict]:
        cursor = self._engine.connection.execute(
            "SELECT * FROM trades ORDER BY timestamp DESC LIMIT ?", (limit,)
        )
        return [dict(row) for row in cursor.fetchall()]

    def get_daily_pnl(self, date_str: str) -> float:
        cursor = self._engine.connection.execute(
            "SELECT SUM(pnl) as total FROM trades WHERE date(timestamp) = ?", (date_str,)
        )
        row = cursor.fetchone()
        return row["total"] or 0.0


class SignalRepository:
    def __init__(self, engine: DatabaseEngine) -> None:
        self._engine = engine

    def save_signal(
        self,
        code: str,
        signal_type: SignalType,
        strength: float = 0.0,
        price: float = 0.0,
        source: str = "",
    ) -> int:
        conn = self._engine.connection
        cursor = conn.execute(
            "INSERT INTO signals (code, signal_type, strength, price, source, timestamp) VALUES (?, ?, ?, ?, ?, ?)",
            (code, signal_type.value, strength, price, source, datetime.now().isoformat()),
        )
        conn.commit()
        return cursor.lastrowid

    def get_signals(self, limit: int = 100) -> list[dict]:
        cursor = self._engine.connection.execute(
            "SELECT * FROM signals ORDER BY timestamp DESC LIMIT ?", (limit,)
        )
        return [dict(row) for row in cursor.fetchall()]


class RiskEventRepository:
    def __init__(self, engine: DatabaseEngine) -> None:
        self._engine = engine

    def save_event(self, event_type: str, detail: str = "") -> int:
        conn = self._engine.connection
        cursor = conn.execute(
            "INSERT INTO risk_events (event_type, detail, timestamp) VALUES (?, ?, ?)",
            (event_type, detail, datetime.now().isoformat()),
        )
        conn.commit()
        return cursor.lastrowid

    def get_events(self, limit: int = 100) -> list[dict]:
        cursor = self._engine.connection.execute(
            "SELECT * FROM risk_events ORDER BY timestamp DESC LIMIT ?", (limit,)
        )
        return [dict(row) for row in cursor.fetchall()]
```

- [ ] **Step 5: Run test to verify it passes**

```bash
pytest tests/test_database.py -v
```
Expected: PASS

- [ ] **Step 6: Commit**

```bash
git add src/database/ tests/test_database.py
git commit -m "feat: database module with SQLite engine and repository layer"
```

---

## Task 6: Market Module

**Files:**
- Create: `src/market/market_base.py`
- Create: `src/market/xt_provider.py`
- Create: `src/market/data_cache.py`
- Create: `tests/test_market.py`

- [ ] **Step 1: Write test for market module**

```python
# tests/test_market.py
import pytest
from datetime import datetime
from src.market.data_cache import DataCache
from src.common.types import Tick, Bar


def test_data_cache_set_get():
    cache = DataCache(ttl_seconds=60)
    tick = Tick(code="510300", last_price=4.5, timestamp=datetime.now())
    cache.set_tick("510300", tick)
    result = cache.get_tick("510300")
    assert result is not None
    assert result.last_price == 4.5


def test_data_cache_expired():
    cache = DataCache(ttl_seconds=0)
    tick = Tick(code="510300", last_price=4.5, timestamp=datetime.now())
    cache.set_tick("510300", tick)
    import time
    time.sleep(0.01)
    result = cache.get_tick("510300")
    assert result is None
```

- [ ] **Step 2: Run test to verify it fails**

```bash
pytest tests/test_market.py -v
```
Expected: FAIL

- [ ] **Step 3: Implement market_base.py**

```python
# src/market/market_base.py
from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Callable

from src.common.types import Bar, Tick


class MarketProvider(ABC):
    @abstractmethod
    def get_realtime_quotes(self, codes: list[str]) -> dict[str, Tick]:
        ...

    @abstractmethod
    def get_history_bars(self, code: str, period: str, count: int) -> list[Bar]:
        ...

    @abstractmethod
    def subscribe(self, codes: list[str], callback: Callable[[Tick], None]) -> None:
        ...

    @abstractmethod
    def connect(self) -> bool:
        ...

    @abstractmethod
    def disconnect(self) -> None:
        ...

    @abstractmethod
    def is_connected(self) -> bool:
        ...
```

- [ ] **Step 4: Implement data_cache.py**

```python
# src/market/data_cache.py
from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Any

from src.common.types import Tick


class DataCache:
    def __init__(self, ttl_seconds: int = 60) -> None:
        self._ttl = ttl_seconds
        self._ticks: dict[str, tuple[Tick, float]] = {}

    def get_tick(self, code: str) -> Tick | None:
        entry = self._ticks.get(code)
        if entry is None:
            return None
        tick, ts = entry
        if time.time() - ts > self._ttl:
            del self._ticks[code]
            return None
        return tick

    def set_tick(self, code: str, tick: Tick) -> None:
        self._ticks[code] = (tick, time.time())

    def clear(self) -> None:
        self._ticks.clear()
```

- [ ] **Step 5: Implement xt_provider.py**

```python
# src/market/xt_provider.py
from __future__ import annotations

from typing import Callable

from loguru import logger

from src.common.types import Bar, Tick
from src.market.data_cache import DataCache
from src.market.market_base import MarketProvider


class XtProvider(MarketProvider):
    def __init__(self, qmt_path: str = "") -> None:
        self._qmt_path = qmt_path
        self._connected = False
        self._cache = DataCache(ttl_seconds=30)

    def connect(self) -> bool:
        try:
            from xtquant import xtdata
            xtdata.connect()
            self._connected = True
            logger.info("xtdata connected")
            return True
        except Exception as e:
            logger.error(f"xtdata connect failed: {e}")
            self._connected = False
            return False

    def disconnect(self) -> None:
        self._connected = False

    def is_connected(self) -> bool:
        return self._connected

    def get_realtime_quotes(self, codes: list[str]) -> dict[str, Tick]:
        result: dict[str, Tick] = {}
        try:
            from xtquant import xtdata
            xtdata.subscribe_quote(codes, period="tick", count=-1)
            raw = xtdata.get_full_tick(codes)
            for code, data in raw.items():
                tick = Tick(
                    code=code,
                    last_price=data.get("lastPrice", 0.0),
                    bid_price=data.get("bidPrice", [0.0])[0] if data.get("bidPrice") else 0.0,
                    ask_price=data.get("askPrice", [0.0])[0] if data.get("askPrice") else 0.0,
                    volume=data.get("volume", 0),
                )
                self._cache.set_tick(code, tick)
                result[code] = tick
        except Exception as e:
            logger.error(f"get_realtime_quotes failed: {e}")
            for code in codes:
                cached = self._cache.get_tick(code)
                if cached:
                    result[code] = cached
        return result

    def get_history_bars(self, code: str, period: str, count: int) -> list[Bar]:
        try:
            from xtquant import xtdata
            xtdata.subscribe_quote(code, period=period, count=count)
            data = xtdata.get_market_data_ex(
                field_list=[], stock_list=[code], period=period, count=count
            )
            bars: list[Bar] = []
            if code in data:
                df = data[code]
                for _, row in df.iterrows():
                    bars.append(Bar(
                        code=code,
                        open=row["open"],
                        high=row["high"],
                        low=row["low"],
                        close=row["close"],
                        volume=row["volume"],
                    ))
            return bars
        except Exception as e:
            logger.error(f"get_history_bars failed for {code}: {e}")
            return []

    def subscribe(self, codes: list[str], callback: Callable[[Tick], None]) -> None:
        try:
            from xtquant import xtdata
            for code in codes:
                xtdata.subscribe_quote(code, period="tick", count=-1)
        except Exception as e:
            logger.error(f"subscribe failed: {e}")
```

- [ ] **Step 6: Run test to verify it passes**

```bash
pytest tests/test_market.py -v
```
Expected: PASS

- [ ] **Step 7: Commit**

```bash
git add src/market/ tests/test_market.py
git commit -m "feat: market module with abstract provider, xtquant impl, and cache"
```

---

## Task 7: Strategy Module

**Files:**
- Create: `src/strategy/strategy_base.py`
- Create: `src/strategy/signal.py`
- Create: `src/strategy/factor.py`
- Create: `src/strategy/etf_rotation.py`
- Create: `src/strategy/strategy_manager.py`
- Create: `tests/test_strategy.py`

- [ ] **Step 1: Write test for factor and strategy**

```python
# tests/test_strategy.py
import pytest
import pandas as pd
import numpy as np
from src.strategy.factor import ma, momentum, trend_strength
from src.common.enums import Direction


def test_ma_basic():
    series = pd.Series([1.0, 2.0, 3.0, 4.0, 5.0])
    result = ma(series, 3)
    assert result.iloc[2] == pytest.approx(2.0)
    assert result.iloc[4] == pytest.approx(4.0)


def test_momentum():
    series = pd.Series([100.0, 105.0, 110.0, 108.0])
    result = momentum(series, 2)
    assert result.iloc[2] == pytest.approx(0.1)


def test_trend_strength():
    close = pd.Series([1.0, 1.1, 1.2, 1.3, 1.4, 1.5, 1.6, 1.7, 1.8, 1.9,
                       2.0, 2.1, 2.2, 2.3, 2.4, 2.5, 2.6, 2.7, 2.8, 2.9, 3.0])
    result = trend_strength(close, short=5, long=20)
    assert len(result) == len(close)
```

- [ ] **Step 2: Run test to verify it fails**

```bash
pytest tests/test_strategy.py -v
```
Expected: FAIL

- [ ] **Step 3: Implement factor.py**

```python
# src/strategy/factor.py
from __future__ import annotations

import numpy as np
import pandas as pd


def ma(series: pd.Series, period: int) -> pd.Series:
    return series.rolling(window=period, min_periods=1).mean()


def momentum(series: pd.Series, period: int) -> pd.Series:
    return series.pct_change(periods=period)


def volatility(series: pd.Series, period: int) -> pd.Series:
    return series.rolling(window=period, min_periods=1).std()


def trend_strength(series: pd.Series, short: int, long: int) -> pd.Series:
    ma_short = ma(series, short)
    ma_long = ma(series, long)
    return (ma_short - ma_long) / ma_long.replace(0, np.nan)
```

- [ ] **Step 4: Implement strategy_base.py and signal.py**

```python
# src/strategy/signal.py
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum

from src.common.enums import Direction, SignalType
from src.common.types import Signal


class SignalStrength(Enum):
    STRONG = 1.0
    MEDIUM = 0.6
    WEAK = 0.3


@dataclass
class StrategySignal(Signal):
    ma5: float = 0.0
    ma10: float = 0.0
    ma20: float = 0.0
    trend_score: float = 0.0
```

```python
# src/strategy/strategy_base.py
from __future__ import annotations

from abc import ABC, abstractmethod

from src.common.types import Bar, Signal


class Strategy(ABC):
    @abstractmethod
    def on_bar(self, bars: dict[str, Bar]) -> list[Signal]:
        ...

    @abstractmethod
    def get_params(self) -> dict:
        ...

    @abstractmethod
    def update_params(self, params: dict) -> None:
        ...
```

- [ ] **Step 5: Implement etf_rotation.py**

```python
# src/strategy/etf_rotation.py
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime

import pandas as pd
from loguru import logger

from src.common.enums import Direction, SignalType, TrendDirection
from src.common.types import Bar, Signal
from src.strategy.factor import ma, trend_strength
from src.strategy.signal import SignalStrength, StrategySignal
from src.strategy.strategy_base import Strategy


@dataclass
class ETFRotationParams:
    ma_periods: list[int] = field(default_factory=lambda: [5, 10, 20])
    trend_threshold: float = 0.02
    max_holdings: int = 3
    rebalance_days: list[int] = field(default_factory=lambda: [0, 4])


class ETFRotationStrategy(Strategy):
    def __init__(self, params: ETFRotationParams | None = None) -> None:
        self._params = params or ETFRotationParams()
        self._holdings: set[str] = set()

    def on_bar(self, bars: dict[str, Bar]) -> list[Signal]:
        signals: list[Signal] = []
        scores: dict[str, float] = {}
        bar_data: dict[str, Bar] = {}

        for code, bar in bars.items():
            if bar.close <= 0:
                continue
            bar_data[code] = bar
            score = self._calc_trend_score(bar)
            if score is not None:
                scores[code] = score

        ranked = sorted(scores.items(), key=lambda x: x[1], reverse=True)
        top_codes: set[str] = set()
        for code, score in ranked[: self._params.max_holdings]:
            if score > self._params.trend_threshold:
                top_codes.add(code)

        for code in top_codes - self._holdings:
            signals.append(StrategySignal(
                code=code,
                direction=Direction.BUY,
                signal_type=SignalType.ENTRY,
                strength=SignalStrength.STRONG.value,
                price=bar_data[code].close,
                source="etf_rotation",
            ))

        for code in self._holdings - top_codes:
            if code in bar_data:
                signals.append(StrategySignal(
                    code=code,
                    direction=Direction.SELL,
                    signal_type=SignalType.EXIT,
                    strength=SignalStrength.STRONG.value,
                    price=bar_data[code].close,
                    source="etf_rotation",
                ))

        self._holdings = top_codes
        return signals

    def _calc_trend_score(self, bar: Bar) -> float | None:
        if bar.close <= 0:
            return None
        score = (bar.close - bar.close * (1 - self._params.trend_threshold)) / bar.close
        return score

    def update_holdings(self, codes: set[str]) -> None:
        self._holdings = codes

    def get_params(self) -> dict:
        return {
            "ma_periods": self._params.ma_periods,
            "trend_threshold": self._params.trend_threshold,
            "max_holdings": self._params.max_holdings,
            "rebalance_days": self._params.rebalance_days,
        }

    def update_params(self, params: dict) -> None:
        for k, v in params.items():
            if hasattr(self._params, k):
                setattr(self._params, k, v)
```

- [ ] **Step 6: Implement strategy_manager.py**

```python
# src/strategy/strategy_manager.py
from __future__ import annotations

from loguru import logger

from src.common.events import Event, EventBus
from src.common.types import Bar, Signal
from src.strategy.strategy_base import Strategy


class StrategyManager:
    def __init__(self, event_bus: EventBus) -> None:
        self._event_bus = event_bus
        self._strategies: list[Strategy] = []
        self._event_bus.subscribe("market_data", self._on_market_data)

    def register(self, strategy: Strategy) -> None:
        self._strategies.append(strategy)
        logger.info(f"Registered strategy: {strategy.__class__.__name__}")

    def _on_market_data(self, event: Event) -> None:
        bars: dict[str, Bar] = event.data.get("bars", {})
        for strategy in self._strategies:
            try:
                signals = strategy.on_bar(bars)
                for signal in signals:
                    self._event_bus.publish(Event(
                        type="signal",
                        data={"signal": signal},
                    ))
            except Exception as e:
                logger.error(f"Strategy {strategy.__class__.__name__} error: {e}")
```

- [ ] **Step 7: Run test to verify it passes**

```bash
pytest tests/test_strategy.py -v
```
Expected: PASS

- [ ] **Step 8: Commit**

```bash
git add src/strategy/ tests/test_strategy.py
git commit -m "feat: strategy module with ETF rotation, factors, and manager"
```

---

## Task 8: Risk Module

**Files:**
- Create: `src/risk/risk_base.py`
- Create: `src/risk/risk_engine.py`
- Create: `src/risk/stop_loss.py`
- Create: `src/risk/position_limit.py`
- Create: `src/risk/breaker.py`
- Create: `src/risk/blacklist.py`
- Create: `tests/test_risk.py`

- [ ] **Step 1: Write test for risk module**

```python
# tests/test_risk.py
import pytest
from datetime import datetime
from src.risk.risk_engine import RiskEngine, RiskContext, RiskResult
from src.risk.stop_loss import StopLossRule
from src.risk.position_limit import PositionLimitRule
from src.risk.breaker import CircuitBreakerRule
from src.risk.blacklist import BlacklistRule
from src.common.types import Signal, Position, Account
from src.common.enums import Direction, SignalType


@pytest.fixture
def risk_engine():
    engine = RiskEngine()
    from src.config.settings import RiskConfig
    config = RiskConfig(
        max_position_ratio=0.30,
        max_drawdown=0.05,
        daily_loss_limit=0.02,
        stop_profit=0.08,
        stop_loss=0.03,
        max_consecutive_losses=3,
        cooldown_minutes=30,
    )
    engine.add_rule(StopLossRule(config))
    engine.add_rule(PositionLimitRule(config))
    engine.add_rule(CircuitBreakerRule(config))
    engine.add_rule(BlacklistRule())
    return engine


def test_buy_signal_passes_with_no_positions(risk_engine):
    signal = Signal(code="510300", direction=Direction.BUY, signal_type=SignalType.ENTRY)
    context = RiskContext(
        positions=[],
        account=Account(total_assets=30000, available=30000),
        daily_trades=[],
    )
    result = risk_engine.check_signal(signal, context)
    assert result.passed is True


def test_position_limit_blocks_when_full(risk_engine):
    positions = [
        Position(code="510300", volume=2000, cost_price=4.5, current_price=4.5, market_value=9000),
        Position(code="510500", volume=2000, cost_price=4.5, current_price=4.5, market_value=9000),
        Position(code="159915", volume=2000, cost_price=4.5, current_price=4.5, market_value=9000),
    ]
    signal = Signal(code="512100", direction=Direction.BUY, signal_type=SignalType.ENTRY)
    context = RiskContext(
        positions=positions,
        account=Account(total_assets=30000, available=3000, market_value=27000),
        daily_trades=[],
    )
    result = risk_engine.check_signal(signal, context)
    assert result.passed is False
    assert "position" in result.rule_name.lower() or "holdings" in result.reason.lower()
```

- [ ] **Step 2: Run test to verify it fails**

```bash
pytest tests/test_risk.py -v
```
Expected: FAIL

- [ ] **Step 3: Implement risk_base.py and risk_engine.py**

```python
# src/risk/risk_base.py
from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime

from src.common.types import Account, Position, Signal, Trade


@dataclass
class RiskContext:
    positions: list[Position] = field(default_factory=list)
    account: Account = field(default_factory=Account)
    daily_trades: list[Trade] = field(default_factory=list)
    current_time: datetime = field(default_factory=datetime.now)
    is_connected: bool = True
    has_market_data: bool = True


@dataclass
class RiskResult:
    passed: bool = True
    reason: str = ""
    rule_name: str = ""


class RiskRule(ABC):
    @abstractmethod
    def check(self, signal: Signal, context: RiskContext) -> RiskResult:
        ...

    @property
    @abstractmethod
    def name(self) -> str:
        ...

    @property
    @abstractmethod
    def priority(self) -> int:
        ...
```

```python
# src/risk/risk_engine.py
from __future__ import annotations

from loguru import logger

from src.common.types import Signal
from src.risk.risk_base import RiskContext, RiskResult, RiskRule


class RiskEngine:
    def __init__(self) -> None:
        self._rules: list[RiskRule] = []

    def add_rule(self, rule: RiskRule) -> None:
        self._rules.append(rule)
        self._rules.sort(key=lambda r: r.priority)

    def check_signal(self, signal: Signal, context: RiskContext) -> RiskResult:
        for rule in self._rules:
            result = rule.check(signal, context)
            if not result.passed:
                logger.bind(module="risk").warning(
                    f"Signal blocked by {rule.name}: {result.reason}"
                )
                return result
        return RiskResult(passed=True, rule_name="all_passed")
```

- [ ] **Step 4: Implement stop_loss.py**

```python
# src/risk/stop_loss.py
from __future__ import annotations

from src.common.enums import Direction, SignalType
from src.common.types import Signal
from src.config.settings import RiskConfig
from src.risk.risk_base import RiskContext, RiskResult, RiskRule


class StopLossRule(RiskRule):
    def __init__(self, config: RiskConfig) -> None:
        self._config = config

    @property
    def name(self) -> str:
        return "stop_loss"

    @property
    def priority(self) -> int:
        return 10

    def check(self, signal: Signal, context: RiskContext) -> RiskResult:
        if signal.direction == Direction.SELL:
            return RiskResult(passed=True, rule_name=self.name)

        for pos in context.positions:
            if pos.volume > 0 and pos.current_price > 0:
                pnl_ratio = (pos.current_price - pos.cost_price) / pos.cost_price
                if pnl_ratio <= -self._config.stop_loss:
                    return RiskResult(
                        passed=False,
                        reason=f"Position {pos.code} loss {pnl_ratio:.2%} exceeds stop_loss {self._config.stop_loss:.2%}",
                        rule_name=self.name,
                    )

        daily_pnl_ratio = 0.0
        if context.account.total_assets > 0:
            daily_pnl_ratio = context.account.daily_pnl / context.account.total_assets
        if daily_pnl_ratio <= -self._config.daily_loss_limit:
            return RiskResult(
                passed=False,
                reason=f"Daily loss {daily_pnl_ratio:.2%} exceeds limit {self._config.daily_loss_limit:.2%}",
                rule_name=self.name,
            )

        return RiskResult(passed=True, rule_name=self.name)
```

- [ ] **Step 5: Implement position_limit.py**

```python
# src/risk/position_limit.py
from __future__ import annotations

from src.common.enums import Direction
from src.common.types import Signal
from src.config.settings import RiskConfig
from src.risk.risk_base import RiskContext, RiskResult, RiskRule


class PositionLimitRule(RiskRule):
    def __init__(self, config: RiskConfig) -> None:
        self._config = config

    @property
    def name(self) -> str:
        return "position_limit"

    @property
    def priority(self) -> int:
        return 20

    def check(self, signal: Signal, context: RiskContext) -> RiskResult:
        if signal.direction == Direction.SELL:
            return RiskResult(passed=True, rule_name=self.name)

        if len(context.positions) >= 3:
            holding_codes = {p.code for p in context.positions}
            if signal.code not in holding_codes:
                return RiskResult(
                    passed=False,
                    reason=f"Max holdings reached ({len(context.positions)}/3)",
                    rule_name=self.name,
                )

        if context.account.total_assets > 0:
            signal_value = signal.price * 100
            ratio = signal_value / context.account.total_assets
            if ratio > self._config.max_position_ratio:
                return RiskResult(
                    passed=False,
                    reason=f"Order ratio {ratio:.2%} exceeds max {self._config.max_position_ratio:.2%}",
                    rule_name=self.name,
                )

        if context.account.available < signal.price * 100:
            return RiskResult(
                passed=False,
                reason="Insufficient available balance",
                rule_name=self.name,
            )

        return RiskResult(passed=True, rule_name=self.name)
```

- [ ] **Step 6: Implement breaker.py**

```python
# src/risk/breaker.py
from __future__ import annotations

import time

from src.common.types import Signal
from src.config.settings import RiskConfig
from src.risk.risk_base import RiskContext, RiskResult, RiskRule


class CircuitBreakerRule(RiskRule):
    def __init__(self, config: RiskConfig) -> None:
        self._config = config
        self._triggered_at: float | None = None
        self._consecutive_losses: int = 0

    @property
    def name(self) -> str:
        return "circuit_breaker"

    @property
    def priority(self) -> int:
        return 5

    def check(self, signal: Signal, context: RiskContext) -> RiskResult:
        if self._triggered_at is not None:
            elapsed = (time.time() - self._triggered_at) / 60
            if elapsed < self._config.cooldown_minutes:
                return RiskResult(
                    passed=False,
                    reason=f"Circuit breaker active, {self._config.cooldown_minutes - elapsed:.0f}min remaining",
                    rule_name=self.name,
                )
            else:
                self._triggered_at = None
                self._consecutive_losses = 0

        if context.account.total_assets > 0:
            drawdown = self._calc_drawdown(context)
            if drawdown >= self._config.max_drawdown:
                self._triggered_at = time.time()
                return RiskResult(
                    passed=False,
                    reason=f"Drawdown {drawdown:.2%} exceeds max {self._config.max_drawdown:.2%}",
                    rule_name=self.name,
                )

        recent_losses = sum(1 for t in context.daily_trades[-self._config.max_consecutive_losses:] if t.pnl < 0)
        if recent_losses >= self._config.max_consecutive_losses:
            self._triggered_at = time.time()
            return RiskResult(
                passed=False,
                reason=f"Consecutive losses ({recent_losses}) reached limit",
                rule_name=self.name,
            )

        return RiskResult(passed=True, rule_name=self.name)

    def _calc_drawdown(self, context: RiskContext) -> float:
        if context.account.total_assets <= 0:
            return 0.0
        return max(0, -context.account.daily_pnl / context.account.total_assets)

    def reset(self) -> None:
        self._triggered_at = None
        self._consecutive_losses = 0
```

- [ ] **Step 7: Implement blacklist.py**

```python
# src/risk/blacklist.py
from __future__ import annotations

from src.common.types import Signal
from src.risk.risk_base import RiskContext, RiskResult, RiskRule


class BlacklistRule(RiskRule):
    def __init__(self, blacklist: set[str] | None = None) -> None:
        self._blacklist: set[str] = blacklist or set()

    @property
    def name(self) -> str:
        return "blacklist"

    @property
    def priority(self) -> int:
        return 1

    def check(self, signal: Signal, context: RiskContext) -> RiskResult:
        if not context.is_connected:
            return RiskResult(
                passed=False,
                reason="Network disconnected, trading suspended",
                rule_name=self.name,
            )

        if not context.has_market_data:
            return RiskResult(
                passed=False,
                reason="Market data abnormal, trading suspended",
                rule_name=self.name,
            )

        if signal.code in self._blacklist:
            return RiskResult(
                passed=False,
                reason=f"ETF {signal.code} is blacklisted",
                rule_name=self.name,
            )

        if signal.price <= 0:
            return RiskResult(
                passed=False,
                reason=f"Invalid price {signal.price} for {signal.code}",
                rule_name=self.name,
            )

        return RiskResult(passed=True, rule_name=self.name)

    def add_to_blacklist(self, code: str) -> None:
        self._blacklist.add(code)

    def remove_from_blacklist(self, code: str) -> None:
        self._blacklist.discard(code)
```

- [ ] **Step 8: Run test to verify it passes**

```bash
pytest tests/test_risk.py -v
```
Expected: PASS

- [ ] **Step 9: Commit**

```bash
git add src/risk/ tests/test_risk.py
git commit -m "feat: risk module with stop-loss, position limit, circuit breaker, blacklist"
```

---

## Task 9: Broker Module

**Files:**
- Create: `src/broker/broker_base.py`
- Create: `src/broker/qmt_client.py`
- Create: `src/broker/order_manager.py`
- Create: `src/broker/trade_callback.py`
- Create: `src/broker/account_manager.py`
- Create: `src/broker/paper_broker.py`
- Create: `tests/test_broker.py`

- [ ] **Step 1: Write test for paper broker**

```python
# tests/test_broker.py
import pytest
from src.broker.paper_broker import PaperBroker
from src.common.enums import Direction, OrderStatus


@pytest.fixture
def broker():
    return PaperBroker(initial_balance=30000.0)


def test_buy_order(broker):
    order_id = broker.buy("510300", 4.5, 1000)
    assert order_id != ""
    positions = broker.get_positions()
    assert any(p.code == "510300" for p in positions)


def test_sell_order(broker):
    broker.buy("510300", 4.5, 1000)
    order_id = broker.sell("510300", 4.6, 1000)
    assert order_id != ""


def test_get_balance(broker):
    balance = broker.get_balance()
    assert balance.total_assets == 30000.0
    assert balance.available == 30000.0


def test_insufficient_balance(broker):
    order_id = broker.buy("510300", 4.5, 100000)
    orders = broker.get_orders()
    assert any(o.status == OrderStatus.REJECTED for o in orders)
```

- [ ] **Step 2: Run test to verify it fails**

```bash
pytest tests/test_broker.py -v
```
Expected: FAIL

- [ ] **Step 3: Implement broker_base.py**

```python
# src/broker/broker_base.py
from __future__ import annotations

from abc import ABC, abstractmethod
from datetime import datetime

from src.common.enums import Direction, OrderStatus
from src.common.types import Account, Order, Position, Trade


class Broker(ABC):
    @abstractmethod
    def buy(self, code: str, price: float, volume: int) -> str:
        ...

    @abstractmethod
    def sell(self, code: str, price: float, volume: int) -> str:
        ...

    @abstractmethod
    def cancel_order(self, order_id: str) -> bool:
        ...

    @abstractmethod
    def get_positions(self) -> list[Position]:
        ...

    @abstractmethod
    def get_balance(self) -> Account:
        ...

    @abstractmethod
    def get_orders(self, status: OrderStatus | None = None) -> list[Order]:
        ...

    @abstractmethod
    def get_trades(self, start: datetime | None = None) -> list[Trade]:
        ...
```

- [ ] **Step 4: Implement qmt_client.py**

```python
# src/broker/qmt_client.py
from __future__ import annotations

import threading
import time

from loguru import logger


class QmtClient:
    def __init__(self, qmt_path: str, account_id: str, account_type: str = "STOCK") -> None:
        self._qmt_path = qmt_path
        self._account_id = account_id
        self._account_type = account_type
        self._connected = False
        self._trader = None
        self._lock = threading.Lock()

    def connect(self) -> bool:
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
            return False

    def disconnect(self) -> None:
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
```

- [ ] **Step 5: Implement order_manager.py**

```python
# src/broker/order_manager.py
from __future__ import annotations

import uuid

from loguru import logger

from src.common.enums import Direction, OrderStatus
from src.common.types import Order


class OrderManager:
    def __init__(self) -> None:
        self._orders: dict[str, Order] = {}
        self._pending_codes: set[str] = set()

    def create_order(self, code: str, direction: Direction, price: float, volume: int) -> Order:
        order_id = uuid.uuid4().hex[:12]
        order = Order(
            order_id=order_id,
            code=code,
            direction=direction,
            price=price,
            volume=volume,
            status=OrderStatus.PENDING,
        )
        self._orders[order_id] = order
        return order

    def is_duplicate(self, code: str, direction: Direction) -> bool:
        key = f"{code}_{direction.value}"
        if key in self._pending_codes:
            return True
        self._pending_codes.add(key)
        return False

    def clear_pending(self, code: str, direction: Direction) -> None:
        key = f"{code}_{direction.value}"
        self._pending_codes.discard(key)

    def update_status(self, order_id: str, status: OrderStatus, filled_volume: int = 0, filled_price: float = 0.0) -> None:
        order = self._orders.get(order_id)
        if order:
            order.status = status
            order.filled_volume = filled_volume
            order.filled_price = filled_price
            if status in (OrderStatus.FILLED, OrderStatus.CANCELLED, OrderStatus.REJECTED):
                self.clear_pending(order.code, order.direction)

    def get_order(self, order_id: str) -> Order | None:
        return self._orders.get(order_id)

    def get_orders(self, status: OrderStatus | None = None) -> list[Order]:
        if status is None:
            return list(self._orders.values())
        return [o for o in self._orders.values() if o.status == status]
```

- [ ] **Step 6: Implement trade_callback.py**

```python
# src/broker/trade_callback.py
from __future__ import annotations

from loguru import logger

from src.common.events import Event, EventBus
from src.common.types import Trade
from src.broker.order_manager import OrderManager
from src.common.enums import Direction, OrderStatus


class TradeCallback:
    def __init__(self, event_bus: EventBus, order_manager: OrderManager) -> None:
        self._event_bus = event_bus
        self._order_manager = order_manager

    def on_order_update(self, order_id: str, status: int, filled_volume: int, filled_price: float) -> None:
        try:
            status_map = {0: OrderStatus.PENDING, 1: OrderStatus.FILLED, 2: OrderStatus.PARTIAL, 3: OrderStatus.CANCELLED, 4: OrderStatus.REJECTED}
            order_status = status_map.get(status, OrderStatus.PENDING)
            self._order_manager.update_status(order_id, order_status, filled_volume, filled_price)
            logger.info(f"Order {order_id} status: {order_status.value}")
        except Exception as e:
            logger.error(f"on_order_update error: {e}")

    def on_trade_report(self, trade: Trade) -> None:
        try:
            self._event_bus.publish(Event(type="trade", data={"trade": trade}))
            logger.info(f"Trade: {trade.code} {trade.direction.value} {trade.volume}@{trade.price}")
        except Exception as e:
            logger.error(f"on_trade_report error: {e}")
```

- [ ] **Step 7: Implement account_manager.py**

```python
# src/broker/account_manager.py
from __future__ import annotations

import time

from loguru import logger

from src.common.types import Account, Position


class AccountManager:
    def __init__(self, cache_ttl: int = 5) -> None:
        self._cache_ttl = cache_ttl
        self._positions_cache: tuple[list[Position], float] | None = None
        self._balance_cache: tuple[Account, float] | None = None

    def get_positions(self, trader, account_id: str, account_type: str) -> list[Position]:
        if self._positions_cache:
            positions, ts = self._positions_cache
            if time.time() - ts < self._cache_ttl:
                return positions
        try:
            positions = []
            if trader:
                raw = trader.query_stock_positions(account_id, account_type)
                for item in raw:
                    positions.append(Position(
                        code=item.stock_code,
                        volume=item.volume,
                        available=item.can_use_volume,
                        cost_price=item.open_price,
                        current_price=item.market_value / item.volume if item.volume > 0 else 0,
                        market_value=item.market_value,
                    ))
            self._positions_cache = (positions, time.time())
            return positions
        except Exception as e:
            logger.error(f"get_positions error: {e}")
            return self._positions_cache[0] if self._positions_cache else []

    def get_balance(self, trader, account_id: str, account_type: str) -> Account:
        if self._balance_cache:
            account, ts = self._balance_cache
            if time.time() - ts < self._cache_ttl:
                return account
        try:
            if trader:
                raw = trader.query_stock_asset(account_id, account_type)
                account = Account(
                    total_assets=raw.total_asset,
                    balance=raw.cash,
                    available=raw.cash - raw.frozen_cash,
                    frozen=raw.frozen_cash,
                    market_value=raw.market_value,
                )
            else:
                account = Account()
            self._balance_cache = (account, time.time())
            return account
        except Exception as e:
            logger.error(f"get_balance error: {e}")
            return self._balance_cache[0] if self._balance_cache else Account()

    def clear_cache(self) -> None:
        self._positions_cache = None
        self._balance_cache = None
```

- [ ] **Step 8: Implement paper_broker.py**

```python
# src/broker/paper_broker.py
from __future__ import annotations

import uuid
from datetime import datetime

from loguru import logger

from src.broker.broker_base import Broker
from src.common.enums import Direction, OrderStatus
from src.common.types import Account, Order, Position, Trade


class PaperBroker(Broker):
    def __init__(self, initial_balance: float = 30000.0, commission_rate: float = 0.0003) -> None:
        self._balance = initial_balance
        self._initial_balance = initial_balance
        self._commission_rate = commission_rate
        self._positions: dict[str, Position] = {}
        self._orders: list[Order] = []
        self._trades: list[Trade] = []

    def buy(self, code: str, price: float, volume: int) -> str:
        cost = price * volume
        commission = max(cost * self._commission_rate, 5.0)
        total_cost = cost + commission

        if total_cost > self._balance:
            order = Order(
                order_id=uuid.uuid4().hex[:12],
                code=code,
                direction=Direction.BUY,
                price=price,
                volume=volume,
                status=OrderStatus.REJECTED,
            )
            self._orders.append(order)
            logger.warning(f"Paper BUY rejected: insufficient balance for {code}")
            return order.order_id

        self._balance -= total_cost

        if code in self._positions:
            pos = self._positions[code]
            total_volume = pos.volume + volume
            pos.cost_price = (pos.cost_price * pos.volume + price * volume) / total_volume
            pos.volume = total_volume
            pos.available = total_volume
        else:
            self._positions[code] = Position(
                code=code,
                volume=volume,
                available=volume,
                cost_price=price,
                current_price=price,
                market_value=price * volume,
            )

        order = Order(
            order_id=uuid.uuid4().hex[:12],
            code=code,
            direction=Direction.BUY,
            price=price,
            volume=volume,
            status=OrderStatus.FILLED,
            filled_volume=volume,
            filled_price=price,
        )
        self._orders.append(order)

        trade = Trade(
            trade_id=uuid.uuid4().hex[:12],
            order_id=order.order_id,
            code=code,
            direction=Direction.BUY,
            price=price,
            volume=volume,
            commission=commission,
        )
        self._trades.append(trade)

        logger.info(f"Paper BUY: {code} {volume}@{price}, commission={commission:.2f}")
        return order.order_id

    def sell(self, code: str, price: float, volume: int) -> str:
        pos = self._positions.get(code)
        if not pos or pos.available < volume:
            order = Order(
                order_id=uuid.uuid4().hex[:12],
                code=code,
                direction=Direction.SELL,
                price=price,
                volume=volume,
                status=OrderStatus.REJECTED,
            )
            self._orders.append(order)
            return order.order_id

        revenue = price * volume
        commission = max(revenue * self._commission_rate, 5.0)
        self._balance += revenue - commission

        pos.volume -= volume
        pos.available -= volume
        pos.market_value = pos.current_price * pos.volume
        if pos.volume == 0:
            del self._positions[code]

        order = Order(
            order_id=uuid.uuid4().hex[:12],
            code=code,
            direction=Direction.SELL,
            price=price,
            volume=volume,
            status=OrderStatus.FILLED,
            filled_volume=volume,
            filled_price=price,
        )
        self._orders.append(order)

        pnl = (price - pos.cost_price) * volume - commission
        trade = Trade(
            trade_id=uuid.uuid4().hex[:12],
            order_id=order.order_id,
            code=code,
            direction=Direction.SELL,
            price=price,
            volume=volume,
            commission=commission,
        )
        self._trades.append(trade)

        logger.info(f"Paper SELL: {code} {volume}@{price}, pnl={pnl:.2f}")
        return order.order_id

    def cancel_order(self, order_id: str) -> bool:
        return False

    def get_positions(self) -> list[Position]:
        return list(self._positions.values())

    def get_balance(self) -> Account:
        market_value = sum(p.market_value for p in self._positions.values())
        return Account(
            total_assets=self._balance + market_value,
            balance=self._balance,
            available=self._balance,
            frozen=0.0,
            market_value=market_value,
        )

    def get_orders(self, status: OrderStatus | None = None) -> list[Order]:
        if status is None:
            return self._orders
        return [o for o in self._orders if o.status == status]

    def get_trades(self, start: datetime | None = None) -> list[Trade]:
        if start is None:
            return self._trades
        return [t for t in self._trades if t.timestamp >= start]
```

- [ ] **Step 9: Run test to verify it passes**

```bash
pytest tests/test_broker.py -v
```
Expected: PASS

- [ ] **Step 10: Commit**

```bash
git add src/broker/ tests/test_broker.py
git commit -m "feat: broker module with QMT client, order/trade management, paper broker"
```

---

## Task 10: Scheduler Module

**Files:**
- Create: `src/scheduler/task_scheduler.py`

- [ ] **Step 1: Implement task_scheduler.py**

```python
# src/scheduler/task_scheduler.py
from __future__ import annotations

from typing import Callable

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from loguru import logger


class TaskScheduler:
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
```

- [ ] **Step 2: Commit**

```bash
git add src/scheduler/
git commit -m "feat: scheduler module with APScheduler wrapper"
```

---

## Task 11: Backtest Module

**Files:**
- Create: `src/backtest/engine.py`
- Create: `src/backtest/data_loader.py`
- Create: `src/backtest/report.py`
- Create: `tests/test_backtest.py`

- [ ] **Step 1: Write test for backtest**

```python
# tests/test_backtest.py
import pytest
from datetime import datetime
from src.backtest.engine import BacktestEngine
from src.broker.paper_broker import PaperBroker
from src.common.types import Bar


def test_backtest_basic():
    broker = PaperBroker(initial_balance=30000.0)
    engine = BacktestEngine(broker=broker)

    days = [
        {"510300": Bar(code="510300", open=4.0, high=4.1, low=3.9, close=4.05, volume=100000)},
        {"510300": Bar(code="510300", open=4.05, high=4.2, low=4.0, close=4.15, volume=120000)},
        {"510300": Bar(code="510300", open=4.15, high=4.3, low=4.1, close=4.25, volume=110000)},
    ]

    class SimpleStrategy:
        def on_bar(self, bars):
            from src.common.enums import Direction, SignalType
            from src.common.types import Signal
            if not broker.get_positions():
                return [Signal(code="510300", direction=Direction.BUY, signal_type=SignalType.ENTRY, price=list(bars.values())[0].close)]
            return []

        def get_params(self):
            return {}

        def update_params(self, params):
            pass

    engine.set_strategy(SimpleStrategy())
    results = engine.run(days)
    assert len(results) > 0
```

- [ ] **Step 2: Run test to verify it fails**

```bash
pytest tests/test_backtest.py -v
```
Expected: FAIL

- [ ] **Step 3: Implement data_loader.py**

```python
# src/backtest/data_loader.py
from __future__ import annotations

from pathlib import Path

import pandas as pd

from src.common.types import Bar


def load_csv_bars(file_path: str, code: str = "") -> list[Bar]:
    df = pd.read_csv(file_path)
    bars: list[Bar] = []
    for _, row in df.iterrows():
        bars.append(Bar(
            code=code or str(row.get("code", "")),
            open=float(row["open"]),
            high=float(row["high"]),
            low=float(row["low"]),
            close=float(row["close"]),
            volume=float(row.get("volume", 0)),
        ))
    return bars


def load_daily_bars(file_path: str, code: str) -> list[dict[str, Bar]]:
    df = pd.read_csv(file_path, parse_dates=["date"])
    days: list[dict[str, Bar]] = []
    for _, row in df.iterrows():
        bar = Bar(
            code=code,
            open=float(row["open"]),
            high=float(row["high"]),
            low=float(row["low"]),
            close=float(row["close"]),
            volume=float(row.get("volume", 0)),
        )
        days.append({code: bar})
    return days
```

- [ ] **Step 4: Implement report.py**

```python
# src/backtest/report.py
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime

import numpy as np


@dataclass
class BacktestResult:
    total_return: float = 0.0
    annual_return: float = 0.0
    max_drawdown: float = 0.0
    sharpe_ratio: float = 0.0
    total_trades: int = 0
    win_rate: float = 0.0
    daily_pnl: list[float] = field(default_factory=list)
    equity_curve: list[float] = field(default_factory=list)


def generate_report(daily_assets: list[float], trades: list[dict]) -> BacktestResult:
    if not daily_assets:
        return BacktestResult()

    initial = daily_assets[0]
    final = daily_assets[-1]
    total_return = (final - initial) / initial

    daily_returns = np.diff(daily_assets) / daily_assets[:-1] if len(daily_assets) > 1 else [0.0]
    annual_return = total_return * 252 / max(len(daily_assets), 1)

    peak = daily_assets[0]
    max_dd = 0.0
    for val in daily_assets:
        if val > peak:
            peak = val
        dd = (peak - val) / peak
        if dd > max_dd:
            max_dd = dd

    sharpe = 0.0
    if len(daily_returns) > 1 and np.std(daily_returns) > 0:
        sharpe = np.mean(daily_returns) / np.std(daily_returns) * np.sqrt(252)

    sell_trades = [t for t in trades if t.get("direction") == "sell"]
    wins = sum(1 for t in sell_trades if t.get("pnl", 0) > 0)
    win_rate = wins / len(sell_trades) if sell_trades else 0.0

    return BacktestResult(
        total_return=total_return,
        annual_return=annual_return,
        max_drawdown=max_dd,
        sharpe_ratio=sharpe,
        total_trades=len(trades),
        win_rate=win_rate,
        equity_curve=daily_assets,
    )
```

- [ ] **Step 5: Implement engine.py**

```python
# src/backtest/engine.py
from __future__ import annotations

from loguru import logger

from src.backtest.report import BacktestResult, generate_report
from src.broker.paper_broker import PaperBroker
from src.common.types import Bar, Signal
from src.risk.risk_base import RiskContext
from src.risk.risk_engine import RiskEngine
from src.strategy.strategy_base import Strategy


class BacktestEngine:
    def __init__(self, broker: PaperBroker, risk_engine: RiskEngine | None = None) -> None:
        self._broker = broker
        self._risk_engine = risk_engine
        self._strategy: Strategy | None = None
        self._daily_assets: list[float] = []
        self._all_trades: list[dict] = []

    def set_strategy(self, strategy: Strategy) -> None:
        self._strategy = strategy

    def set_risk_engine(self, risk_engine: RiskEngine) -> None:
        self._risk_engine = risk_engine

    def run(self, daily_bars: list[dict[str, Bar]]) -> BacktestResult:
        if not self._strategy:
            raise ValueError("Strategy not set")

        for bars in daily_bars:
            signals = self._strategy.on_bar(bars)

            for signal in signals:
                if self._risk_engine:
                    context = RiskContext(
                        positions=self._broker.get_positions(),
                        account=self._broker.get_balance(),
                    )
                    result = self._risk_engine.check_signal(signal, context)
                    if not result.passed:
                        logger.debug(f"Backtest signal blocked: {result.reason}")
                        continue

                from src.common.enums import Direction
                if signal.direction == Direction.BUY:
                    volume = int(self._broker.get_balance().available * 0.9 / max(signal.price, 0.01) / 100) * 100
                    if volume > 0:
                        self._broker.buy(signal.code, signal.price, volume)
                elif signal.direction == Direction.SELL:
                    positions = self._broker.get_positions()
                    for pos in positions:
                        if pos.code == signal.code and pos.available > 0:
                            self._broker.sell(signal.code, signal.price, pos.available)

            balance = self._broker.get_balance()
            self._daily_assets.append(balance.total_assets)

        trades = [{"direction": t.direction.value, "pnl": 0.0} for t in self._broker.get_trades()]
        return generate_report(self._daily_assets, trades)
```

- [ ] **Step 6: Run test to verify it passes**

```bash
pytest tests/test_backtest.py -v
```
Expected: PASS

- [ ] **Step 7: Commit**

```bash
git add src/backtest/ tests/test_backtest.py
git commit -m "feat: backtest module with engine, data loader, and report"
```

---

## Task 12: Dashboard Module

**Files:**
- Create: `src/dashboard/app.py`
- Create: `src/dashboard/pages/portfolio.py`
- Create: `src/dashboard/pages/signals.py`
- Create: `src/dashboard/pages/trades.py`
- Create: `src/dashboard/pages/risk.py`
- Create: `src/dashboard/components/charts.py`
- Create: `src/dashboard/components/metrics.py`

- [ ] **Step 1: Implement components/metrics.py**

```python
# src/dashboard/components/metrics.py
import streamlit as st


def render_account_metrics(total_assets: float, daily_pnl: float, position_count: int, max_drawdown: float) -> None:
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Total Assets", f"¥{total_assets:,.2f}")
    pnl_color = "normal" if daily_pnl >= 0 else "inverse"
    col2.metric("Daily P&L", f"¥{daily_pnl:,.2f}", delta=f"{daily_pnl:+.2f}")
    col3.metric("Positions", str(position_count))
    col4.metric("Max Drawdown", f"{max_drawdown:.2%}")
```

- [ ] **Step 2: Implement components/charts.py**

```python
# src/dashboard/components/charts.py
import plotly.graph_objects as go
import pandas as pd


def render_equity_curve(dates: list, values: list) -> None:
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=dates, y=values, mode="lines", name="Equity"))
    fig.update_layout(title="Equity Curve", xaxis_title="Date", yaxis_title="Value (¥)", height=400)
    st.plotly_chart(fig, use_container_width=True)


def render_kline_with_ma(df: pd.DataFrame, code: str) -> None:
    fig = go.Figure(data=[go.Candlestick(
        x=df["date"],
        open=df["open"],
        high=df["high"],
        low=df["low"],
        close=df["close"],
        name=code,
    )])
    if "ma5" in df.columns:
        fig.add_trace(go.Scatter(x=df["date"], y=df["ma5"], mode="lines", name="MA5"))
    if "ma20" in df.columns:
        fig.add_trace(go.Scatter(x=df["date"], y=df["ma20"], mode="lines", name="MA20"))
    fig.update_layout(title=f"{code} K-Line", height=500)
    st.plotly_chart(fig, use_container_width=True)
```

```python
# src/dashboard/components/__init__.py (empty, already created in Task 1)
```

- [ ] **Step 3: Implement pages/portfolio.py**

```python
# src/dashboard/pages/portfolio.py
import streamlit as st
from src.dashboard.components.metrics import render_account_metrics


def render_portfolio_page(db_engine) -> None:
    st.header("Portfolio Overview")

    render_account_metrics(
        total_assets=st.session_state.get("total_assets", 30000.0),
        daily_pnl=st.session_state.get("daily_pnl", 0.0),
        position_count=st.session_state.get("position_count", 0),
        max_drawdown=st.session_state.get("max_drawdown", 0.0),
    )

    st.subheader("Current Positions")
    positions = st.session_state.get("positions", [])
    if positions:
        import pandas as pd
        df = pd.DataFrame([p.__dict__ for p in positions])
        st.dataframe(df, use_container_width=True)
    else:
        st.info("No open positions")
```

- [ ] **Step 4: Implement pages/signals.py**

```python
# src/dashboard/pages/signals.py
import streamlit as st
from src.database.repository import SignalRepository


def render_signals_page(db_engine) -> None:
    st.header("Signal History")
    repo = SignalRepository(db_engine)
    signals = repo.get_signals(limit=100)
    if signals:
        import pandas as pd
        df = pd.DataFrame(signals)
        st.dataframe(df, use_container_width=True)
    else:
        st.info("No signals recorded")
```

- [ ] **Step 5: Implement pages/trades.py**

```python
# src/dashboard/pages/trades.py
import streamlit as st
from src.database.repository import TradeRepository


def render_trades_page(db_engine) -> None:
    st.header("Trade History")
    repo = TradeRepository(db_engine)
    trades = repo.get_trades(limit=100)
    if trades:
        import pandas as pd
        df = pd.DataFrame(trades)
        st.dataframe(df, use_container_width=True)
    else:
        st.info("No trades recorded")
```

- [ ] **Step 6: Implement pages/risk.py**

```python
# src/dashboard/pages/risk.py
import streamlit as st
from src.database.repository import RiskEventRepository


def render_risk_page(db_engine) -> None:
    st.header("Risk Status")

    col1, col2 = st.columns(2)
    col1.metric("Circuit Breaker", "Active" if st.session_state.get("breaker_active") else "Normal")
    col2.metric("Consecutive Losses", str(st.session_state.get("consecutive_losses", 0)))

    st.subheader("Risk Events")
    repo = RiskEventRepository(db_engine)
    events = repo.get_events(limit=50)
    if events:
        import pandas as pd
        df = pd.DataFrame(events)
        st.dataframe(df, use_container_width=True)
    else:
        st.info("No risk events")
```

- [ ] **Step 7: Implement app.py**

```python
# src/dashboard/app.py
import streamlit as st
from src.database.engine import DatabaseEngine
from src.dashboard.pages.portfolio import render_portfolio_page
from src.dashboard.pages.signals import render_signals_page
from src.dashboard.pages.trades import render_trades_page
from src.dashboard.pages.risk import render_risk_page


def create_dashboard(db_path: str = "data/sentinel.db") -> None:
    st.set_page_config(page_title="SentinelTrade", layout="wide")
    st.title("SentinelTrade Dashboard")

    db_engine = DatabaseEngine(db_path)
    db_engine.init_tables()

    page = st.sidebar.selectbox("Navigation", ["Portfolio", "Signals", "Trades", "Risk"])

    if st.sidebar.button("Refresh"):
        st.rerun()

    if page == "Portfolio":
        render_portfolio_page(db_engine)
    elif page == "Signals":
        render_signals_page(db_engine)
    elif page == "Trades":
        render_trades_page(db_engine)
    elif page == "Risk":
        render_risk_page(db_engine)


if __name__ == "__main__":
    create_dashboard()
```

- [ ] **Step 8: Commit**

```bash
git add src/dashboard/
git commit -m "feat: dashboard module with Streamlit pages and chart components"
```

---

## Task 13: AI Placeholder Module

**Files:**
- Create: `src/ai/ai_base.py`
- Create: `src/ai/feature_engine.py`

- [ ] **Step 1: Implement ai_base.py and feature_engine.py**

```python
# src/ai/ai_base.py
from __future__ import annotations

from abc import ABC, abstractmethod

import numpy as np


class AIModel(ABC):
    @abstractmethod
    def predict(self, features: np.ndarray) -> float:
        ...

    @abstractmethod
    def train(self, X: np.ndarray, y: np.ndarray) -> None:
        ...

    @abstractmethod
    def save(self, path: str) -> None:
        ...

    @abstractmethod
    def load(self, path: str) -> None:
        ...
```

```python
# src/ai/feature_engine.py
from __future__ import annotations

import numpy as np
import pandas as pd

from src.strategy.factor import ma, momentum, volatility


def extract_features(df: pd.DataFrame) -> np.ndarray:
    close = df["close"]
    features = pd.DataFrame()
    features["ma5_ratio"] = close / ma(close, 5)
    features["ma10_ratio"] = close / ma(close, 10)
    features["ma20_ratio"] = close / ma(close, 20)
    features["momentum_5"] = momentum(close, 5)
    features["momentum_10"] = momentum(close, 10)
    features["volatility_10"] = volatility(close, 10)
    features["volatility_20"] = volatility(close, 20)
    return features.fillna(0).values
```

- [ ] **Step 2: Commit**

```bash
git add src/ai/
git commit -m "feat: AI placeholder module with abstract model and feature engine"
```

---

## Task 14: Main Entry Point

**Files:**
- Create: `main.py`

- [ ] **Step 1: Implement main.py**

```python
# main.py
"""
SentinelTrade - A-Share ETF Automated Trading System

Startup flow:
1. Load config (.env + config.yaml)
2. Initialize logger (loguru)
3. Initialize database (SQLite)
4. Initialize EventBus
5. Initialize modules (Market, Strategy, Risk, Broker)
6. Register event handlers
7. Start scheduler (APScheduler)
8. Keep running
"""
import signal
import sys
import time

from loguru import logger

from src.broker.account_manager import AccountManager
from src.broker.order_manager import OrderManager
from src.broker.paper_broker import PaperBroker
from src.broker.trade_callback import TradeCallback
from src.common.events import Event, EventBus
from src.config.loader import load_config
from src.config.settings import AppConfig
from src.database.engine import DatabaseEngine
from src.database.repository import RiskEventRepository, SignalRepository, TradeRepository
from src.risk.blacklist import BlacklistRule
from src.risk.breaker import CircuitBreakerRule
from src.risk.position_limit import PositionLimitRule
from src.risk.risk_engine import RiskEngine
from src.risk.stop_loss import StopLossRule
from src.scheduler.task_scheduler import TaskScheduler
from src.strategy.etf_rotation import ETFRotationStrategy, ETFRotationParams
from src.strategy.strategy_manager import StrategyManager
from src.utils.logger import setup_logger
from src.utils.notify import create_notifier


class SentinelTrade:
    def __init__(self, config_path: str = "config.yaml") -> None:
        self.config = load_config(config_path)
        setup_logger(
            level=self.config.logging.level,
            rotation=self.config.logging.rotation,
            retention=self.config.logging.retention,
        )
        logger.info("SentinelTrade initializing...")

        self.db_engine = DatabaseEngine(self.config.database.path)
        self.db_engine.init_tables()
        self.trade_repo = TradeRepository(self.db_engine)
        self.signal_repo = SignalRepository(self.db_engine)
        self.risk_event_repo = RiskEventRepository(self.db_engine)

        self.event_bus = EventBus()
        self.notifier = create_notifier("log")

        self._setup_risk()
        self._setup_strategy()
        self._setup_broker()
        self._setup_scheduler()

        self._running = False

    def _setup_risk(self) -> None:
        self.risk_engine = RiskEngine()
        self.risk_engine.add_rule(BlacklistRule())
        self.risk_engine.add_rule(CircuitBreakerRule(self.config.risk))
        self.risk_engine.add_rule(StopLossRule(self.config.risk))
        self.risk_engine.add_rule(PositionLimitRule(self.config.risk))
        logger.info("Risk engine initialized")

    def _setup_strategy(self) -> None:
        params = ETFRotationParams(
            ma_periods=self.config.strategy.ma_periods,
            trend_threshold=self.config.strategy.trend_threshold,
            max_holdings=self.config.strategy.max_holdings,
            rebalance_days=self.config.strategy.rebalance_days,
        )
        strategy = ETFRotationStrategy(params)
        self.strategy_manager = StrategyManager(self.event_bus)
        self.strategy_manager.register(strategy)
        logger.info("Strategy manager initialized")

    def _setup_broker(self) -> None:
        self.order_manager = OrderManager()
        self.account_manager = AccountManager()
        self.broker = PaperBroker(initial_balance=30000.0)
        self.trade_callback = TradeCallback(self.event_bus, self.order_manager)

        self.event_bus.subscribe("trade", self._on_trade)
        self.event_bus.subscribe("signal", self._on_signal)
        logger.info("Broker initialized")

    def _setup_scheduler(self) -> None:
        self.scheduler = TaskScheduler()
        self.scheduler.add_daily_task(self.config.scheduler.scan_time, self._scan_market, "scan_market")
        self.scheduler.add_daily_task(self.config.scheduler.rebalance_time, self._rebalance, "rebalance")
        self.scheduler.add_daily_task(self.config.scheduler.close_check_time, self._close_check, "close_check")
        self.scheduler.add_daily_task(self.config.scheduler.settle_time, self._settle, "settle")
        logger.info("Scheduler initialized")

    def _scan_market(self) -> None:
        logger.info("Scanning market...")
        codes = [etf.code for etf in self.config.etf_pool]
        quotes = {}
        for code in codes:
            quotes[code] = type("Bar", (), {"code": code, "open": 0, "high": 0, "low": 0, "close": 0, "volume": 0})()
        self.event_bus.publish(Event(type="market_data", data={"bars": quotes}))

    def _rebalance(self) -> None:
        logger.info("Rebalancing...")

    def _close_check(self) -> None:
        logger.info("Close check...")

    def _settle(self) -> None:
        logger.info("Settling daily...")

    def _on_trade(self, event: Event) -> None:
        trade = event.data.get("trade")
        if trade:
            self.trade_repo.save_trade(
                code=trade.code,
                direction=trade.direction,
                price=trade.price,
                volume=trade.volume,
                commission=trade.commission,
            )

    def _on_signal(self, event: Event) -> None:
        signal = event.data.get("signal")
        if signal:
            self.signal_repo.save_signal(
                code=signal.code,
                signal_type=signal.signal_type,
                strength=signal.strength,
                source=signal.source,
            )

    def run(self) -> None:
        self._running = True
        self.scheduler.start()
        logger.info("SentinelTrade started. Press Ctrl+C to stop.")

        def _shutdown(sig, frame):
            logger.info("Shutting down...")
            self._running = False
            self.scheduler.stop()
            self.db_engine.close()
            sys.exit(0)

        signal.signal(signal.SIGINT, _shutdown)
        signal.signal(signal.SIGTERM, _shutdown)

        while self._running:
            time.sleep(1)


if __name__ == "__main__":
    app = SentinelTrade()
    app.run()
```

- [ ] **Step 2: Commit**

```bash
git add main.py
git commit -m "feat: main entry point with full module integration"
```

---

## Task 15: README

**Files:**
- Create: `README.md`

- [ ] **Step 1: Create README.md**

```markdown
# SentinelTrade

A-Share ETF Automated Trading System

## Quick Start

```bash
pip install -r requirements.txt
cp .env.example .env  # Edit with your QMT credentials
python main.py
```

## Dashboard

```bash
streamlit run src/dashboard/app.py
```

## Project Structure

- `src/config/` - Configuration management
- `src/common/` - Shared types, enums, EventBus
- `src/database/` - SQLite persistence
- `src/market/` - Market data (xtquant)
- `src/strategy/` - Trading strategies
- `src/risk/` - Risk control engine
- `src/broker/` - Order execution
- `src/scheduler/` - Task scheduling
- `src/dashboard/` - Web dashboard
- `src/backtest/` - Backtesting engine
- `src/ai/` - AI model placeholder
- `src/utils/` - Utilities

## Configuration

Edit `config.yaml` for strategy/risk parameters.
Edit `.env` for QMT credentials and secrets.
```

- [ ] **Step 2: Commit**

```bash
git add README.md
git commit -m "docs: add README with quick start and project structure"
```
