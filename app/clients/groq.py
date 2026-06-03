import os
import httpx
from typing import Dict, Any, List
import logging

logger = logging.getLogger("app.clients.groq")

GROQ_API_KEY = os.environ.get("GROQ_API_KEY")
# Default Groq URL may vary by provider; try common endpoints if not configured.
GROQ_API_URL = os.environ.get("GROQ_API_URL", "")
GROQ_MODEL = os.environ.get("GROQ_MODEL", "llama-3.3-70b-versatile")


async def call_groq(system_prompt: str, messages: List[Dict[str, str]], menu_json: Dict[str, Any]) -> Dict[str, Any]:
    """
    Thin wrapper for a Groq-like LLM API. If `GROQ_API_KEY` is missing this returns a simulated reply for local testing.
    Adjust `GROQ_API_URL` if your provider's endpoint differs.
    """
    if not GROQ_API_KEY:
        last_user = next((m for m in reversed(messages) if m.get("role") == "user"), {})
        content = last_user.get("content", "Hello")
        return {"content": f"(simulated Groq reply) {content}"}

    headers = {"Authorization": f"Bearer {GROQ_API_KEY}", "Content-Type": "application/json"}

    # Provider-native payload (some Groq installations use custom shapes)
    provider_payload = {
        "system": system_prompt,
        "messages": messages,
        "menu": menu_json,
    }

    # OpenAI-compatible chat payload (widely supported)
    openai_payload = {
        "model": GROQ_MODEL,
        "messages": [{"role": "system", "content": system_prompt}] + [m for m in messages],
        "temperature": 0.3,
        "max_tokens": 512,
    }

    # Candidate URLs to try (primary then common chat/completions fallbacks).
    # If GROQ_API_URL isn't set, try a curated list of known Groq endpoints.
    if GROQ_API_URL:
        candidates = [GROQ_API_URL]
        if not GROQ_API_URL.endswith("/chat/completions"):
            candidates.append(GROQ_API_URL.rstrip("/") + "/chat/completions")
            candidates.append(GROQ_API_URL.rstrip("/").replace("/generate", "/chat/completions"))
    else:
        candidates = [
            "https://api.groq.com/v1/chat/completions",
            "https://api.groq.dev/v1/chat/completions",
            "https://api.groq.dev/v1/generate",
            "https://api.groq.ai/v1/chat/completions",
        ]

    async with httpx.AsyncClient(timeout=30) as client:
        last_exc_text = None
        for url in candidates:
            try:
                # First try provider-native payload
                logger.debug("Trying Groq URL %s with provider payload", url)
                resp = await client.post(url, json=provider_payload, headers=headers)
                if resp.status_code == 404:
                    logger.debug("Got 404 from %s; will try next candidate", url)
                    last_exc_text = resp.text
                    continue
                resp.raise_for_status()
                j = resp.json()
                logger.debug("Groq response (provider payload) from %s: %s", url, j)
                break
            except Exception as e:
                # try OpenAI-compatible payload as a fallback for this URL
                try:
                    logger.debug("Provider payload failed for %s, trying OpenAI-style payload", url)
                    resp = await client.post(url, json=openai_payload, headers=headers)
                    if resp.status_code == 404:
                        logger.debug("Got 404 on OpenAI payload from %s", url)
                        last_exc_text = resp.text
                        continue
                    resp.raise_for_status()
                    j = resp.json()
                    logger.debug("Groq response (openai payload) from %s: %s", url, j)
                    break
                except Exception as e2:
                    try:
                        last_exc_text = e2.response.text if getattr(e2, 'response', None) is not None else str(e2)
                    except Exception:
                        last_exc_text = str(e2)
                    logger.exception("Attempt to call %s failed: %s", url, e2)
                    continue

        else:
            # all candidates failed
            logger.error("All Groq endpoint candidates failed; last response: %s", last_exc_text)
            last_user = next((m for m in reversed(messages) if m.get('role') == 'user'), {})
            content = last_user.get('content', 'Hello')
            return {"content": f"(simulated Groq reply - unable to reach API) {content}"}

    # Normalize various possible response shapes from providers into {'content': text}
    # Common forms: {'content': 'text'}, {'text': '...'}, {'choices': [{'text': '...'}]}, {'outputs': [{'content': [{'text': '...'}]}]}
    try:
        if isinstance(j, dict) and 'content' in j and isinstance(j['content'], str):
            return {'content': j['content']}
        if isinstance(j, dict) and 'text' in j:
            return {'content': j['text']}
        if isinstance(j, dict) and 'choices' in j and isinstance(j['choices'], list) and len(j['choices'])>0:
            c = j['choices'][0]
            if isinstance(c, dict) and 'text' in c:
                return {'content': c['text']}
        if isinstance(j, dict) and 'outputs' in j and isinstance(j['outputs'], list) and len(j['outputs'])>0:
            out = j['outputs'][0]
            if isinstance(out, dict) and 'content' in out and isinstance(out['content'], list) and len(out['content'])>0:
                part = out['content'][0]
                if isinstance(part, dict) and 'text' in part:
                    return {'content': part['text']}
    except Exception:
        pass

    # Fallback: stringify whatever the provider returned
    return {'content': str(j)}
