import json
import os
from dataclasses import dataclass, field

import requests
from dotenv import load_dotenv

load_dotenv()

OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"


class FormatFailure(Exception):
    """Raised when a model's response can't be parsed as valid JSON after retries."""


@dataclass
class OpenRouterClient:
    api_key: str | None = field(default=None)
    base_url: str = OPENROUTER_URL

    def __post_init__(self) -> None:
        self.api_key = self.api_key or os.environ.get("OPENROUTER_API_KEY")
        if not self.api_key:
            raise ValueError(
                "OPENROUTER_API_KEY not set (pass api_key= or set it in .env)"
            )

    def complete(self, model: str, system_prompt: str, user_prompt: str) -> str:
        response = requests.post(
            self.base_url,
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
            },
            json={
                "model": model,
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
            },
            timeout=60,
        )
        response.raise_for_status()
        data = response.json()
        return data["choices"][0]["message"]["content"]

    def complete_json(
        self,
        model: str,
        system_prompt: str,
        user_prompt: str,
        max_retries: int = 3,
    ) -> dict:
        last_error: Exception | None = None
        for _ in range(max_retries):
            raw = self.complete(model, system_prompt, user_prompt)
            try:
                return _extract_json(raw)
            except ValueError as exc:
                last_error = exc
                continue
        raise FormatFailure(
            f"Model {model} failed to produce valid JSON after "
            f"{max_retries} attempts: {last_error}"
        )


def _extract_json(text: str) -> dict:
    text = text.strip()
    if text.startswith("```"):
        text = text.strip("`")
        if text.startswith("json"):
            text = text[4:]
        text = text.strip()
    try:
        return json.loads(text)
    except json.JSONDecodeError as exc:
        raise ValueError(f"Could not parse JSON: {exc}") from exc
