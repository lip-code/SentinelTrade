"""Risk engine: executes risk rules in priority order."""
from __future__ import annotations

from loguru import logger

from src.common.types import Signal
from src.risk.risk_base import RiskContext, RiskResult, RiskRule


class RiskEngine:
    """Chain-of-rules risk engine. Rejects if any rule fails."""

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

    def get_rules(self) -> list[RiskRule]:
        return list(self._rules)
