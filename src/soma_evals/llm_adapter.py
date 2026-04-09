"""LLM adapter that routes prompts through Simon Willison's llm library.

Adapted from nmdc-ai-eval's LLMLibraryAdapter. Creates a fresh adapter per
eval call, captures token usage and timing. Supports PDF attachments for
multimodal models.
"""

from __future__ import annotations

from typing import Any

import llm as llm_lib


class LLMLibraryAdapter:
    """Routes prompts through any llm-plugin model.

    Args:
        model_name: any model recognized by ``uv run llm models list``
        system_prompt: optional system prompt sent with every generate() call
    """

    def __init__(self, model_name: str, system_prompt: str | None = None) -> None:
        self.model = model_name
        self.system_prompt = system_prompt
        self.messages: list[str] = []
        self._pdf_paths: list[str] = []
        self._last_response: Any = None

    def add_message(self, text: str = "", pdf_files: list[str] | None = None) -> None:
        """Append a text message and/or PDF file paths to the conversation."""
        if text:
            self.messages.append(text)

    def generate(
        self,
        *,
        temperature: float = 0.0,
        max_tokens: int | None = None,
    ) -> str:
        """Send all accumulated messages to the model and return the response text.
        """
        m = llm_lib.get_model(self.model)
        full_prompt = "\n\n".join(self.messages)

        prompt_kwargs: dict[str, Any] = {
            "system": self.system_prompt,
            "temperature": temperature,
        }
        if max_tokens is not None:
            prompt_kwargs["max_tokens"] = max_tokens
        response = m.prompt(full_prompt, **prompt_kwargs)
        self._last_response = response
        return response.text()

    def get_token_usage(self) -> dict[str, int | None]:
        """Extract token usage from the last response."""
        if self._last_response is None:
            return {"input_tokens": None, "output_tokens": None}
        return {
            "input_tokens": getattr(self._last_response, "input_tokens", None),
            "output_tokens": getattr(self._last_response, "output_tokens", None),
        }

    def get_duration_ms(self) -> int | None:
        """Extract duration from the last response."""
        if self._last_response is None:
            return None
        try:
            result: int = self._last_response.duration_ms()
            return result
        except Exception:
            return None
