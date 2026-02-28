from __future__ import annotations

from dataclasses import dataclass
import asyncio
import json
from typing import Any, Dict, Optional, Union

import google.generativeai as genai

from app.core.config import settings


class StubAIClient:
    """Fallback client used when no real AI backend is configured.

    This preserves the previous stub behaviour so the backend keeps working
    without any API keys configured.
    """

    async def chat(self, prompt: str, context: Optional[str] = None) -> str:
        snippet = (context or "")[:120]
        return f"(stubbed AI) You said: {prompt[:200]}. Context: {snippet}"

    async def openai_json(  # type: ignore[override]
        self,
        *,
        system_prompt: str,
        user_prompt: str,
        json_schema_hint: Dict[str, Any],
    ) -> Dict[str, Any]:
        return {
            **json_schema_hint,
            "_stubbed": True,
            "note": "No AI API key configured; returning stubbed JSON.",
        }


@dataclass
class GeminiClient:
    """AI client backed by Google Gemini."""

    model_name: str = settings.gemini_model

    def __post_init__(self) -> None:
        if not settings.gemini_api_key:
            # This should not normally happen because get_ai_client() guards it,
            # but we keep the check to avoid misconfiguration issues.
            raise RuntimeError("GEMINI_API_KEY is not configured.")

        genai.configure(api_key=settings.gemini_api_key)
        self._model = genai.GenerativeModel(self.model_name)

    async def chat(self, prompt: str, context: Optional[str] = None) -> str:
        """Chat endpoint used for AI summary and general chat."""
        merged_prompt = prompt
        if context:
            merged_prompt = (
                "Context:\n"
                f"{context}\n\n"
                "User prompt:\n"
                f"{prompt}"
            )

        try:
            loop = asyncio.get_running_loop()

            def _call() -> str:
                response = self._model.generate_content(merged_prompt)
                # Debug visibility into raw Gemini response shape.
                # Avoid printing full content to keep logs small.
                try:
                    print("Gemini chat raw response type:", type(response))
                except Exception:
                    pass
                text = getattr(response, "text", None)
                if not text and hasattr(response, "candidates"):
                    # Fallback extraction for older gemini SDKs.
                    candidate = (response.candidates or [None])[0]
                    if candidate and candidate.content and candidate.content.parts:
                        text = "".join(p.text or "" for p in candidate.content.parts)
                return (text or "").strip()

            reply = await loop.run_in_executor(None, _call)
            if not reply:
                print("Gemini chat returned empty text; falling back to stub response.")
                snippet = (context or "")[:120]
                return f"(stubbed AI) You said: {prompt[:200]}. Context: {snippet}"
            return reply
        except Exception as exc:
            # Log the underlying Gemini error for debugging.
            print("Gemini chat exception:", repr(exc))
            # Clear error handling – log-like message in response while
            # still keeping the backend functional.
            snippet = (context or "")[:120]
            return (
                "(stubbed AI due to Gemini error) "
                f"You said: {prompt[:200]}. Context: {snippet}. "
                "Reason: Gemini request failed."
            )

    async def openai_json(  # type: ignore[override]
        self,
        *,
        system_prompt: str,
        user_prompt: str,
        json_schema_hint: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Return a structured JSON object using Gemini.

        The name is kept for backwards-compatibility with existing callers.
        """
        full_prompt = (
            f"{system_prompt.strip()}\n\n"
            f"{user_prompt.strip()}\n\n"
            "Return ONLY valid JSON. No markdown. No extra keys."
        )

        try:
            loop = asyncio.get_running_loop()

            def _call() -> str:
                response = self._model.generate_content(full_prompt)
                try:
                    print("Gemini JSON raw response type:", type(response))
                except Exception:
                    pass
                text = getattr(response, "text", None)
                if not text and hasattr(response, "candidates"):
                    candidate = (response.candidates or [None])[0]
                    if candidate and candidate.content and candidate.content.parts:
                        text = "".join(p.text or "" for p in candidate.content.parts)
                return (text or "").strip()

            content = await loop.run_in_executor(None, _call)
        except Exception as exc:
            print("Gemini JSON exception:", repr(exc))
            return {
                **json_schema_hint,
                "_stubbed": True,
                "note": "Gemini request failed; returning stubbed JSON.",
            }

        parsed = _safe_json_loads(content)
        if parsed is None:
            return {
                **json_schema_hint,
                "_parse_error": True,
                "raw": content[:2000],
            }
        return parsed


AIClientType = Union[GeminiClient, StubAIClient]


def get_ai_client() -> AIClientType:
    """Return a Gemini-backed client if configured, else a stub client.

    This ensures the backend keeps working when GEMINI_API_KEY is missing.
    Also prints which implementation is currently active for quick debugging.
    """
    if settings.gemini_api_key:
        try:
            print("Using GeminiClient")  # temporary debug log
            return GeminiClient()
        except Exception:
            # If Gemini misconfigured, fall back to stub instead of failing hard.
            print("Using StubAIClient (Gemini init failed)")  # temporary debug log
            return StubAIClient()

    print("Using StubAIClient (no GEMINI_API_KEY)")  # temporary debug log
    return StubAIClient()


def _safe_json_loads(text: str) -> Optional[Dict[str, Any]]:
    try:
        obj = json.loads(text)
        return obj if isinstance(obj, dict) else None
    except Exception:
        pass

    # fallback: extract first {...} block
    start = text.find("{")
    end = text.rfind("}")
    if start == -1 or end == -1 or end <= start:
        return None
    try:
        obj = json.loads(text[start : end + 1])
        return obj if isinstance(obj, dict) else None
    except Exception:
        return None

