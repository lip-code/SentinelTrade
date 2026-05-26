"""Stop-loss and stop-profit risk rules."""
from __future__ import annotations

from src.common.enums import Direction
from src.common.types import Signal
from src.config.settings import RiskConfig
from src.risk.risk_base import RiskContext, RiskResult, RiskRule


class StopLossRule(RiskRule):
    """Checks per-position stop-loss and daily loss limit."""

    def __init__(self, config: RiskConfig) -> None:
        self._config = config

    @property
    def name(self) -> str:
        return "stop_loss"

    @property
    def priority(self) -> int:
        return 10

    def check(self, signal: Signal, context: RiskContext) -> RiskResult:
        # Stop-loss doesn't block sell signals
        if signal.direction == Direction.SELL:
            return RiskResult(passed=True, rule_name=self.name)

        # Check per-position stop-loss
        for pos in context.positions:
            if pos.volume > 0 and pos.current_price > 0 and pos.cost_price > 0:
                pnl_ratio = (pos.current_price - pos.cost_price) / pos.cost_price
                if pnl_ratio <= -self._config.stop_loss:
                    return RiskResult(
                        passed=False,
                        reason=f"Position {pos.code} loss {pnl_ratio:.2%} exceeds stop_loss {self._config.stop_loss:.2%}",
                        rule_name=self.name,
                    )

        # Check daily loss limit
        if context.account.total_assets > 0:
            daily_pnl_ratio = context.account.daily_pnl / context.account.total_assets
            if daily_pnl_ratio <= -self._config.daily_loss_limit:
                return RiskResult(
                    passed=False,
                    reason=f"Daily loss {daily_pnl_ratio:.2%} exceeds limit {self._config.daily_loss_limit:.2%}",
                    rule_name=self.name,
                )

        return RiskResult(passed=True, rule_name=self.name)


class StopProfitRule(RiskRule):
    """Generates sell signals when positions hit stop-profit target."""

    def __init__(self, config: RiskConfig) -> None:
        self._config = config

    @property
    def name(self) -> str:
        return "stop_profit"

    @property
    def priority(self) -> int:
        return 15

    def check(self, signal: Signal, context: RiskContext) -> RiskResult:
        # This rule doesn't block signals, it's informational
        return RiskResult(passed=True, rule_name=self.name)

    def get_stop_profit_targets(self, context: RiskContext) -> list[str]:
        """Return codes that have hit stop-profit target."""
        targets = []
        for pos in context.positions:
            if pos.volume > 0 and pos.current_price > 0 and pos.cost_price > 0:
                pnl_ratio = (pos.current_price - pos.cost_price) / pos.cost_price
                if pnl_ratio >= self._config.stop_profit:
                    targets.append(pos.code)
        return targets
