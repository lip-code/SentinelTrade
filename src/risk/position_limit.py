"""Position limit risk rules."""
from __future__ import annotations

from src.common.enums import Direction
from src.common.types import Signal
from src.config.settings import RiskConfig
from src.risk.risk_base import RiskContext, RiskResult, RiskRule


class PositionLimitRule(RiskRule):
    """Checks max holdings count, single position ratio, and available balance."""

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

        # Max holdings check (3 for A-share ETF small capital)
        holding_codes = {p.code for p in context.positions if p.volume > 0}
        if signal.code not in holding_codes and len(holding_codes) >= 3:
            return RiskResult(
                passed=False,
                reason=f"Max holdings reached ({len(holding_codes)}/3)",
                rule_name=self.name,
            )

        # Single position ratio check
        if context.account.total_assets > 0 and signal.price > 0:
            signal_value = signal.price * 100  # Minimum lot
            ratio = signal_value / context.account.total_assets
            if ratio > self._config.max_position_ratio:
                return RiskResult(
                    passed=False,
                    reason=f"Order ratio {ratio:.2%} exceeds max {self._config.max_position_ratio:.2%}",
                    rule_name=self.name,
                )

        # Available balance check
        if signal.price > 0 and context.account.available < signal.price * 100:
            return RiskResult(
                passed=False,
                reason=f"Insufficient balance: need {signal.price * 100:.2f}, have {context.account.available:.2f}",
                rule_name=self.name,
            )

        return RiskResult(passed=True, rule_name=self.name)
