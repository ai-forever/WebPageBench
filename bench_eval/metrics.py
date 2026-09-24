"""DeepEval metrics for WebPageBench mock evaluation."""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from deepeval.metrics import BaseMetric
from deepeval.test_case import LLMTestCase, SingleTurnParams


def _dab_check(metadata: Optional[Dict[str, Any]]) -> Dict[str, Any]:
    if not metadata:
        return {}
    return metadata.get("dab_check") or {}


class DABConditionsMetric(BaseMetric):
    """
    Score task success from WebPageBench telemetry condition checks.

    Uses grouped OR logic for conditions with a `group` field.
    """

    _required_params = [SingleTurnParams.METADATA]

    def __init__(self, threshold: float = 1.0, async_mode: bool = False):
        self.threshold = threshold
        self.async_mode = async_mode
        self.strict_mode = False
        self.verbose_mode = True
        self.include_reason = True
        self.score: Optional[float] = None
        self.reason: Optional[str] = None
        self.success: Optional[bool] = None
        self.error: Optional[str] = None

    @property
    def __name__(self):
        return "WebPageBench Conditions"

    def measure(self, test_case: LLMTestCase, *args, **kwargs) -> float:
        dab = _dab_check(test_case.metadata)
        self.score = float(dab.get("score", 0.0))
        self.success = bool(dab.get("all_passed", False)) and self.score >= self.threshold
        passed = dab.get("passed", 0)
        total = dab.get("total", 0)
        failed = dab.get("failed_conditions") or []
        if failed:
            self.reason = (
                f"WebPageBench: {passed}/{total} checks passed. Failed: {', '.join(failed[:5])}"
            )
        else:
            self.reason = f"WebPageBench: {passed}/{total} checks passed."
        if test_case.metadata and test_case.metadata.get("agent_error"):
            self.reason = f"{self.reason} Agent error: {test_case.metadata['agent_error']}"
        return self.score

    async def a_measure(self, test_case: LLMTestCase, *args, **kwargs) -> float:
        return self.measure(test_case, *args, **kwargs)

    def is_successful(self) -> bool:
        if self.error:
            return False
        return bool(self.success)


class AgentCompletionMetric(BaseMetric):
    """Whether browser-use reported the task as done."""

    _required_params = [SingleTurnParams.METADATA]

    def __init__(self, threshold: float = 1.0, async_mode: bool = False):
        self.threshold = threshold
        self.async_mode = async_mode
        self.strict_mode = False
        self.verbose_mode = True
        self.include_reason = True
        self.score: Optional[float] = None
        self.reason: Optional[str] = None
        self.success: Optional[bool] = None
        self.error: Optional[str] = None

    @property
    def __name__(self):
        return "Agent Completion"

    def measure(self, test_case: LLMTestCase, *args, **kwargs) -> float:
        agent = (test_case.metadata or {}).get("agent") or {}
        if agent.get("skipped"):
            self.score = 0.0
            self.success = False
            self.reason = agent.get("reason", "agent skipped")
            return self.score
        if agent.get("error"):
            self.score = 0.0
            self.success = False
            self.reason = agent["error"]
            return self.score
        done = bool(agent.get("is_done"))
        self.score = 1.0 if done else 0.0
        self.success = self.score >= self.threshold
        steps = agent.get("steps", 0)
        self.reason = f"Agent finished={done}, steps={steps}"
        return self.score

    async def a_measure(self, test_case: LLMTestCase, *args, **kwargs) -> float:
        return self.measure(test_case, *args, **kwargs)

    def is_successful(self) -> bool:
        if self.error:
            return False
        return bool(self.success)


AGENT_BENCH_METRICS: List[BaseMetric] = [
    DABConditionsMetric(threshold=1.0),
    AgentCompletionMetric(threshold=1.0),
]
