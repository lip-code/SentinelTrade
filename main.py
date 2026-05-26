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
from datetime import datetime

from loguru import logger

from src.broker.account_manager import AccountManager
from src.broker.order_manager import OrderManager
from src.broker.paper_broker import PaperBroker
from src.broker.xt_broker import XtBroker
from src.broker.trade_callback import TradeCallback
from src.common.enums import Direction, SignalType
from src.common.events import Event, EventBus
from src.common.types import Account, Bar, Position, Signal
from src.config.loader import load_config
from src.config.settings import AppConfig
from src.database.engine import DatabaseEngine
from src.database.repository import PnlRepository, RiskEventRepository, SignalRepository, TradeRepository
from src.market.xt_provider import XtProvider
from src.risk.blacklist import BlacklistRule
from src.risk.breaker import CircuitBreakerRule
from src.risk.position_limit import PositionLimitRule
from src.risk.risk_base import RiskContext
from src.risk.risk_engine import RiskEngine
from src.risk.stop_loss import StopLossRule, StopProfitRule
from src.scheduler.task_scheduler import TaskScheduler
from src.strategy.etf_rotation import ETFRotationParams, ETFRotationStrategy
from src.strategy.strategy_manager import StrategyManager
from src.utils.logger import setup_logger
from src.utils.notify import create_notifier


class SentinelTrade:
    """Main application orchestrator."""

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
        self.pnl_repo = PnlRepository(self.db_engine)
        self.risk_event_repo = RiskEventRepository(self.db_engine)

        self.event_bus = EventBus()
        self.notifier = create_notifier("log")

        self._setup_market()
        self._setup_risk()
        self._setup_strategy()
        self._setup_broker()
        self._setup_scheduler()

        self._running = False
        self._peak_assets: float = 0.0

    def _setup_market(self) -> None:
        self.market = XtProvider(qmt_path=self.config.broker.qmt_path)
        if self.config.broker.broker_type == "live":
            self.market.connect()
        logger.info("Market provider initialized")

    def _setup_risk(self) -> None:
        self.risk_engine = RiskEngine()
        self.risk_engine.add_rule(BlacklistRule())
        self.risk_engine.add_rule(CircuitBreakerRule(self.config.risk))
        self.risk_engine.add_rule(StopLossRule(self.config.risk))
        self.risk_engine.add_rule(PositionLimitRule(self.config.risk))
        self.stop_profit_rule = StopProfitRule(self.config.risk)
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

        broker_type = self.config.broker.broker_type
        qmt_path = self.config.broker.qmt_path
        account_id = self.config.broker.qmt_account
        account_type = self.config.broker.qmt_account_type

        if broker_type == "live" and qmt_path and account_id:
            self.broker = XtBroker(
                qmt_path=qmt_path,
                account_id=account_id,
                account_type=account_type,
                event_bus=self.event_bus,
            )
            connected = self.broker.connect()
            if not connected:
                logger.warning("QMT connection failed, falling back to PaperBroker")
                self.broker = PaperBroker(initial_balance=30000.0)
            else:
                logger.info(f"Live broker connected: {account_id}")
        else:
            self.broker = PaperBroker(initial_balance=30000.0)
            logger.info("Paper broker initialized")

        self.trade_callback = TradeCallback(self.event_bus, self.order_manager)
        self.event_bus.subscribe("trade", self._on_trade)
        self.event_bus.subscribe("signal", self._on_signal)

    def _setup_scheduler(self) -> None:
        self.scheduler = TaskScheduler()
        self.scheduler.add_daily_task(self.config.scheduler.scan_time, self._scan_market, "scan_market")
        self.scheduler.add_daily_task(self.config.scheduler.rebalance_time, self._rebalance, "rebalance")
        self.scheduler.add_daily_task(self.config.scheduler.close_check_time, self._close_check, "close_check")
        self.scheduler.add_daily_task(self.config.scheduler.settle_time, self._settle, "settle")
        logger.info("Scheduler initialized")

    # ── Scheduled Tasks ──────────────────────────────────────────────

    def _scan_market(self) -> None:
        """Fetch real quotes for ETF pool and trigger strategy evaluation."""
        logger.info("Scanning market...")
        codes = [etf.code for etf in self.config.etf_pool]

        # Get real market data
        bars: dict[str, Bar] = {}
        if self.market.is_connected():
            ticks = self.market.get_realtime_quotes(codes)
            for code, tick in ticks.items():
                bars[code] = Bar(
                    code=code,
                    open=tick.last_price,  # Tick only has last_price
                    high=tick.last_price,
                    low=tick.last_price,
                    close=tick.last_price,
                    volume=tick.volume,
                )
        else:
            # Fallback: try history bars
            for code in codes:
                history = self.market.get_history_bars(code, period="1d", count=1)
                if history:
                    bars[code] = history[-1]

        if not bars:
            logger.warning("No market data available")
            return

        logger.info(f"Got quotes for {len(bars)} ETFs")
        self.event_bus.publish(Event(type="market_data", data={"bars": bars}))

    def _rebalance(self) -> None:
        """Execute signals: risk check → broker order."""
        logger.info("Rebalancing...")

        # Get current state
        positions = self.broker.get_positions()
        account = self.broker.get_balance()

        # Update peak assets for drawdown tracking
        if account.total_assets > self._peak_assets:
            self._peak_assets = account.total_assets

    def _close_check(self) -> None:
        """Pre-close check: stop-loss and stop-profit for open positions."""
        logger.info("Running close check...")
        positions = self.broker.get_positions()
        account = self.broker.get_balance()

        if not positions:
            return

        context = RiskContext(positions=positions, account=account)

        # Check stop-profit targets
        stop_profit_codes = self.stop_profit_rule.get_stop_profit_targets(context)
        for code in stop_profit_codes:
            pos = next((p for p in positions if p.code == code), None)
            if pos and pos.available > 0:
                logger.info(f"Stop-profit triggered for {code}, selling {pos.available} shares")
                self.broker.sell(code, pos.current_price, pos.available)

    def _settle(self) -> None:
        """Daily settlement: record PnL, update DB."""
        logger.info("Settling daily...")
        account = self.broker.get_balance()
        today = datetime.now().strftime("%Y-%m-%d")

        drawdown = 0.0
        if self._peak_assets > 0:
            drawdown = (self._peak_assets - account.total_assets) / self._peak_assets

        self.pnl_repo.save_daily_pnl(
            date_str=today,
            total_assets=account.total_assets,
            pnl=account.daily_pnl,
            drawdown=drawdown,
        )
        logger.info(
            f"Daily settle: assets={account.total_assets:.2f}, "
            f"pnl={account.daily_pnl:.2f}, drawdown={drawdown:.2%}"
        )

    # ── Event Handlers ───────────────────────────────────────────────

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
        """Handle signal: risk check → execute order."""
        sig: Signal = event.data.get("signal")
        if not sig:
            return

        # Save signal to DB
        self.signal_repo.save_signal(
            code=sig.code,
            signal_type=sig.signal_type,
            strength=sig.strength,
            source=sig.source,
        )

        # Risk check
        positions = self.broker.get_positions()
        account = self.broker.get_balance()
        context = RiskContext(positions=positions, account=account)
        result = self.risk_engine.check_signal(sig, context)

        if not result.passed:
            logger.warning(f"Signal rejected by {result.rule_name}: {result.reason}")
            self.risk_event_repo.save_event(result.rule_name, result.reason)
            self.notifier.send("Signal Rejected", f"{sig.code}: {result.reason}")
            return

        # Execute order
        if sig.direction == Direction.BUY:
            # Calculate volume: use 90% of available cash, round to 100
            if sig.price > 0:
                max_value = account.available * 0.9
                volume = int(max_value / sig.price / 100) * 100
                if volume >= 100:
                    order_id = self.broker.buy(sig.code, sig.price, volume)
                    logger.info(f"BUY executed: {sig.code} {volume}@{sig.price}, order={order_id}")
            else:
                logger.warning(f"BUY skipped: invalid price for {sig.code}")

        elif sig.direction == Direction.SELL:
            pos = next((p for p in positions if p.code == sig.code), None)
            if pos and pos.available > 0:
                order_id = self.broker.sell(sig.code, sig.price, pos.available)
                logger.info(f"SELL executed: {sig.code} {pos.available}@{sig.price}, order={order_id}")

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
