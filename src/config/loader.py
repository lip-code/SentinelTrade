from __future__ import annotations

import os
from pathlib import Path

import yaml
from dotenv import load_dotenv

from src.config.settings import (
    AppConfig,
    BacktestConfig,
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

    backtest_raw = raw.get("backtest", {})
    backtest = BacktestConfig(**backtest_raw) if backtest_raw else BacktestConfig()

    scheduler_raw = raw.get("scheduler", {})
    scheduler = SchedulerConfig(**scheduler_raw) if scheduler_raw else SchedulerConfig()

    db_raw = raw.get("database", {})
    db_path = os.getenv("DB_PATH", db_raw.get("path", "data/sentinel.db"))
    database = DatabaseConfig(path=db_path)

    log_raw = raw.get("logging", {})
    logging_cfg = LoggingConfig(**log_raw) if log_raw else LoggingConfig()

    broker = BrokerConfig(
        broker_type=raw.get("broker", {}).get("broker_type", "paper"),
        qmt_path=os.getenv("QMT_PATH", ""),
        qmt_account=os.getenv("QMT_ACCOUNT", ""),
        qmt_account_type=os.getenv("QMT_ACCOUNT_TYPE", "STOCK"),
    )

    return AppConfig(
        etf_pool=etf_pool,
        strategy=strategy,
        risk=risk,
        backtest=backtest,
        scheduler=scheduler,
        database=database,
        logging=logging_cfg,
        broker=broker,
    )
