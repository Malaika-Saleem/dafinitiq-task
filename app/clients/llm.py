from .groq import call_groq as call_llm_impl
from typing import Dict, Any, List


async def call_llm(system_prompt: str, messages: List[Dict[str, str]], menu_json: Dict[str, Any]) -> Dict[str, Any]:
    """Delegate LLM calls to the Groq client implementation."""
    return await call_llm_impl(system_prompt, messages, menu_json)
