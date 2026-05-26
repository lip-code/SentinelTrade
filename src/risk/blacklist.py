"""Blacklist and anomaly detection rules."""
from __future__ import annotations

from src.common.types import Signal
from src.risk.risk_base import RiskContext, RiskResult, RiskRule


class BlacklistRule(RiskRule):
    """Blocks blacklisted ETFs and detects network/market anomalies."""

    def __init__(self, blacklist: set[str] | None = None) -> None:
        self._blacklist: set[str] = blacklist or set()

    @property
    def name(self) -> str:
        return "blacklist"

    @property
    def priority(self) -> int:
        return 1  # Highest priority: check first

    def check(self, signal: Signal, context: RiskContext) -> RiskResult:
        # Network connectivity check
        if not context.is_connected:
            return RiskResult(
                passed=False,
                reason="Network disconnected, trading suspended",
                rule_name=self.name,
            )

        # Market data check
        if not context.has_market_data:
            return RiskResult(
                passed=False,
                reason="Market data abnormal, trading suspended",
                rule_name=self.name,
            )

        # Blacklist check
        if signal.code in self._blacklist:
            return RiskResult(
                passed=False,
                reason=f"ETF {signal.code} is blacklisted",
                rule_name=self.name,
            )

        # Price sanity check
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
