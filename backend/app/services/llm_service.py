import json
import re
from typing import Any

from groq import Groq

from app.config import settings


class LLMError(Exception):
    """Raised when the LLM call fails or returns invalid JSON."""


def _extract_json(text: str) -> dict[str, Any]:
    """Parse JSON from the model reply, even if it has ```json fences or extra text."""

    cleaned = text.strip()
    cleaned = re.sub(
        r"^```(?:json)?\s*|\s*```$",
        "",
        cleaned,
        flags=re.IGNORECASE,
    )

    try:
        data = json.loads(cleaned)
    except json.JSONDecodeError:
        start = cleaned.find("{")
        end = cleaned.rfind("}")

        if start == -1 or end <= start:
            raise LLMError("Model reply did not contain valid JSON")

        try:
            data = json.loads(cleaned[start : end + 1])
        except json.JSONDecodeError as exc:
            raise LLMError(f"Model reply was not valid JSON: {exc}") from exc

    if not isinstance(data, dict):
        raise LLMError("Model reply JSON must be an object")

    return data


class LLMService:
    """Single place where all agents talk to Groq."""

    def __init__(self) -> None:
        if not settings.GROQ_API_KEY:
            raise LLMError("GROQ_API_KEY is missing. Add it to backend/.env")

        self.client = Groq(
            api_key=settings.GROQ_API_KEY,
            timeout=settings.LLM_TIMEOUT_SECONDS,
            max_retries=settings.LLM_MAX_RETRIES,
        )
        self.model = settings.GROQ_MODEL

    def generate_json(
        self,
        system_prompt: str,
        user_prompt: str,
        temperature: float = 0.1,
    ) -> dict[str, Any]:
        """Ask the model a question and get a JSON object back."""

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": (
                            system_prompt
                            + "\n\nRespond ONLY with a valid JSON object. "
                            "No extra text."
                        ),
                    },
                    {"role": "user", "content": user_prompt},
                ],
                temperature=temperature,
                response_format={"type": "json_object"},
            )
        except Exception as exc:
            raise LLMError(f"Groq API call failed: {exc}") from exc

        content = response.choices[0].message.content or ""
        return _extract_json(content)

    def list_models(self) -> list[str]:
        """Return model IDs available for this API key."""

        try:
            models = self.client.models.list()
        except Exception as exc:
            raise LLMError(f"Could not list Groq models: {exc}") from exc

        return sorted(model.id for model in models.data)