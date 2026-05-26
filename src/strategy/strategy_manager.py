"""Strategy orchestrator: manages multiple strategies and routes signals."""
from __future__ import annotations

from loguru import logger

from src.common.events import Event, EventBus
from src.common.types import Bar, Signal
from src.strategy.strategy_base import Strategy


class StrategyManager:
    """Registers strategies, distributes market data, and publishes signals."""

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
