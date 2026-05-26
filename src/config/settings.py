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
class BacktestConfig:
    initial_cash: float = 30000.0
    commission_rate: float = 0.0003
    commission_min: float = 5.0
    slippage_perc: float = 0.001
    slippage_fixed: float = 0.0
    stamp_tax: float = 0.0
    start_date: str = ""
    end_date: str = ""


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
    broker_type: str = "paper"  # "paper" or "live"
    qmt_path: str = ""
    qmt_account: str = ""
    qmt_account_type: str = "STOCK"


@dataclass
class AppConfig:
    etf_pool: list[EtfItem] = field(default_factory=list)
    strategy: StrategyConfig = field(default_factory=StrategyConfig)
    risk: RiskConfig = field(default_factory=RiskConfig)
    backtest: BacktestConfig = field(default_factory=BacktestConfig)
    scheduler: SchedulerConfig = field(default_factory=SchedulerConfig)
    database: DatabaseConfig = field(default_factory=DatabaseConfig)
    logging: LoggingConfig = field(default_factory=LoggingConfig)
    broker: BrokerConfig = field(default_factory=BrokerConfig)
