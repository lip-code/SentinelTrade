"""Circuit breaker and consecutive loss protection."""
from __future__ import annotations

import time

from src.common.types import Signal
from src.config.settings import RiskConfig
from src.risk.risk_base import RiskContext, RiskResult, RiskRule


class CircuitBreakerRule(RiskRule):
    """Halts trading on max drawdown or consecutive losses."""

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
        # Check if breaker is active and cooldown hasn't expired
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

        # Check max drawdown
        if context.account.total_assets > 0:
            drawdown = self._calc_drawdown(context)
            if drawdown >= self._config.max_drawdown:
                self._triggered_at = time.time()
                return RiskResult(
                    passed=False,
                    reason=f"Drawdown {drawdown:.2%} exceeds max {self._config.max_drawdown:.2%}",
                    rule_name=self.name,
                )

        # Check consecutive losses
        recent_trades = context.daily_trades[-self._config.max_consecutive_losses:]
        recent_losses = sum(1 for t in recent_trades if t.pnl < 0)
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

    @property
    def is_active(self) -> bool:
        if self._triggered_at is None:
            return False
        elapsed = (time.time() - self._triggered_at) / 60
        return elapsed < self._config.cooldown_minutes
