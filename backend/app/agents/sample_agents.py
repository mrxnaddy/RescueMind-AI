from typing import Any

from app.agents.base import BaseAgent
from app.agents.echo_agent import EchoAgent
from app.schemas.agent import AgentResult


class FlakyEchoAgent(EchoAgent):
    """Test-only: fails the first N calls, then works (tests retries)."""

    def __init__(self, fail_times: int = 1) -> None:
        self.fail_times = fail_times
        self.calls = 0

    def process(self, input_data: dict[str, Any]) -> AgentResult:
        self.calls += 1

        if self.calls <= self.fail_times:
            raise RuntimeError(f"Temporary failure (call {self.calls})")

        return super().process(input_data)


class WordLengthAgent(BaseAgent):
    """Test-only: reads echo_agent's output to prove results are passed on."""

    name = "word_length_agent"

    def process(self, input_data: dict[str, Any]) -> AgentResult:
        previous = input_data.get("previous_results", {}).get("echo_agent")

        if previous is None:
            raise ValueError("echo_agent result not found in previous_results")

        count = previous["word_count"]
        category = "short" if count < 10 else "long"

        return AgentResult(
            agent_name=self.name,
            output={"length_category": category},
            explanation=f"The report has {count} words, so it is {category}.",
            supporting_evidence=[f"echo_agent reported word_count={count}"],
            missing_information=[],
            requires_human_verification=False,
        )