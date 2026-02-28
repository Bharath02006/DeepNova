from typing import Any, Dict, List

from app.models.schemas import ChatMessage, ChatRequest
from app.utils.ai_client import get_ai_client


async def chat_with_ai(payload: ChatRequest) -> ChatMessage:
    """Delegate chat to the configured AI client.

    For the hackathon, this can be a simple wrapper around an LLM API
    or a stub that returns canned responses.
    """
    client = get_ai_client()
    last_user_message = next(
        (m for m in reversed(payload.messages) if m.role == "user"),
        None,
    )

    prompt = last_user_message.content if last_user_message else ""
    reply_text = await client.chat(prompt=prompt, context=payload.context_snippet)

    return ChatMessage(role="assistant", content=reply_text)


async def explain_code(code: str) -> Dict[str, Any]:
    client = get_ai_client()
    schema_hint = {
        "overview": "",
        "key_points": [],
        "potential_risks": [],
    }
    return await client.openai_json(
        system_prompt="You explain source code clearly for a hackathon team.",
        user_prompt=(
            "Explain what this code does.\n"
            "Return JSON with: overview (string), key_points (string[]), potential_risks (string[]).\n\n"
            f"{code[:6000]}"
        ),
        json_schema_hint=schema_hint,
    )


async def suggest_improvements(code: str) -> Dict[str, Any]:
    client = get_ai_client()
    schema_hint = {
        "improvements": [
            {"title": "", "why": "", "how": "", "risk": "low"},
        ]
    }
    return await client.openai_json(
        system_prompt="You suggest practical code improvements for a 16-hour hackathon.",
        user_prompt=(
            "Suggest improvements for this code. Keep suggestions actionable and minimal.\n"
            "Return JSON with: improvements: [{title, why, how, risk(low|medium|high)}].\n\n"
            f"{code[:6000]}"
        ),
        json_schema_hint=schema_hint,
    )


async def autofix_code(code: str) -> Dict[str, Any]:
    client = get_ai_client()
    schema_hint = {
        "fixed_code": code,
        "diff_summary": [],
        "changes": [{"title": "", "description": ""}],
    }
    return await client.openai_json(
        system_prompt=(
            "You safely apply minimal fixes to improve code quality. "
            "Optimize the code to reduce time complexity where reasonable and "
            "improve maintainability without changing external behaviour."
        ),
        user_prompt=(
            "Autofix this code with minimal changes. Keep behavior the same.\n"
            "Optimize the code to reduce time complexity if possible and improve maintainability.\n"
            "Return ONLY valid JSON. No markdown.\n"
            "Return JSON with: fixed_code (string), diff_summary (string[]), "
            "changes: [{title, description}].\n\n"
            f"{code[:6000]}"
        ),
        json_schema_hint=schema_hint,
    )


async def chat_with_code(code: str, user_query: str) -> Dict[str, Any]:
    client = get_ai_client()
    schema_hint = {
        "answer": "",
        "next_steps": [],
        "references": [],
    }
    return await client.openai_json(
        system_prompt="You answer developer questions grounded in the provided code.",
        user_prompt=(
            "Given the code and question, respond.\n"
            "Return JSON with: answer (string), next_steps (string[]), references (string[]).\n\n"
            f"QUESTION:\n{user_query}\n\nCODE:\n{code[:6000]}"
        ),
        json_schema_hint=schema_hint,
    )

