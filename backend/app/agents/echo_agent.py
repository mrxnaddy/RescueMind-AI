from typing import Any

from app.agents.base import BaseAgent
from app.schemas.agent import AgentResult


class EchoAgent(BaseAgent):
    """Test-only agent used to verify the BaseAgent logging works."""

    name = "echo_agent"

    def process(self, input_data: dict[str, Any]) -> AgentResult:
        if input_data.get("simulate_error"):
            raise ValueError("Simulated failure for testing")

        text = str(input_data.get("text", "")).strip()
        words = text.split()

        return AgentResult(
            agent_name=self.name,
            output={
                "word_count": len(words),
                "character_count": len(text),
            },
            explanation=f"Counted {len(words)} words in the provided text.",
            supporting_evidence=[f"Input text: {text[:100]}"],
            missing_information=[],
            requires_human_verification=False,
        )