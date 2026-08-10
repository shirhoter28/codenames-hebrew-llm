import json
import os
from dataclasses import dataclass, field

import requests
from dotenv import load_dotenv
from tenacity import Retrying, retry_if_exception, stop_after_attempt, wait_exponential

load_dotenv()

OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"


class FormatFailure(Exception):
    """Raised when a model's response can't be parsed as valid JSON after retries.

    ``raw_response`` carries the last raw text the model produced (when there is
    one), so an exhausted-retries failure can be diagnosed from the logs instead
    of only showing a generic message.
    """

    def __init__(self, message: str, raw_response: str | None = None) -> None:
        super().__init__(message)
        self.raw_response = raw_response


def _is_retryable_transport_error(exc: BaseException) -> bool:
    """Retry transport hiccups and server/rate-limit errors, never client errors.

    4xx responses other than 429 (400 bad request, 401 unauthorized, ...) are
    permanent — retrying them just burns API calls.
    """
    if isinstance(exc, requests.exceptions.HTTPError):
        status = getattr(exc.response, "status_code", None)
        if status is None:
            return False
        return status == 429 or status >= 500
    return isinstance(exc, requests.exceptions.RequestException)


@dataclass
class OpenRouterClient:
    api_key: str | None = field(default=None)
    base_url: str = OPENROUTER_URL
    max_tokens: int = 1024
    max_attempts: int = 4
    retry_backoff: float = 0.5

    def __post_init__(self) -> None:
        self.api_key = self.api_key or os.environ.get("OPENROUTER_API_KEY")
        if not self.api_key:
            raise ValueError(
                "OPENROUTER_API_KEY not set (pass api_key= or set it in .env)"
            )

    def complete(self, model: str, system_prompt: str, user_prompt: str) -> str:
        retryer = Retrying(
            retry=retry_if_exception(_is_retryable_transport_error),
            stop=stop_after_attempt(self.max_attempts),
            wait=wait_exponential(multiplier=self.retry_backoff, max=30),
            reraise=True,
        )
        return retryer(self._complete_once, model, system_prompt, user_prompt)

    def _complete_once(self, model: str, system_prompt: str, user_prompt: str) -> str:
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
                "max_tokens": self.max_tokens,
                "reasoning": {"enabled": False},
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
        last_raw: str | None = None
        for _ in range(max_retries):
            raw = self.complete(model, system_prompt, user_prompt)
            last_raw = raw
            try:
                return _extract_json(raw)
            except ValueError as exc:
                last_error = exc
                continue
        raise FormatFailure(
            f"Model {model} failed to produce valid JSON after "
            f"{max_retries} attempts: {last_error}",
            raw_response=last_raw,
        )


def _first_balanced_object(text: str) -> str | None:
    """Return the first balanced ``{...}`` substring, or None if there isn't one.

    Handles nested braces and braces that appear inside JSON string literals.
    """
    start = text.find("{")
    if start == -1:
        return None
    depth = 0
    in_string = False
    escaped = False
    for index in range(start, len(text)):
        char = text[index]
        if in_string:
            if escaped:
                escaped = False
            elif char == "\\":
                escaped = True
            elif char == '"':
                in_string = False
            continue
        if char == '"':
            in_string = True
        elif char == "{":
            depth += 1
        elif char == "}":
            depth -= 1
            if depth == 0:
                return text[start : index + 1]
    return None


def _extract_json(text: str) -> dict:
    text = text.strip()
    if text.startswith("```"):
        text = text.strip("`")
        if text.startswith("json"):
            text = text[4:]
        text = text.strip()
    try:
        parsed = json.loads(text)
    except json.JSONDecodeError as exc:
        # Models sometimes wrap the object in prose ("הנה הרמז שלי: {...}").
        candidate = _first_balanced_object(text)
        if candidate is None:
            raise ValueError(f"Could not parse JSON: {exc}") from exc
        try:
            parsed = json.loads(candidate)
        except json.JSONDecodeError as inner:
            raise ValueError(f"Could not parse JSON: {inner}") from inner
    if not isinstance(parsed, dict):
        raise ValueError(f"expected a JSON object, got {type(parsed).__name__}")
    return parsed
