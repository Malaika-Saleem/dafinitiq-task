import os
import os
import httpx
import base64
from typing import Optional, Tuple

import logging

ELEVENLABS_API_KEY = os.environ.get("ELEVENLABS_API_KEY")
ELEVENLABS_VOICE = os.environ.get("ELEVENLABS_VOICE_ID", "alloy")

logger = logging.getLogger("app.clients.tts")


async def synthesize_text_to_base64(text: str) -> Optional[Tuple[str, str]]:
    """
    Call ElevenLabs TTS and return tuple (base64_audio, mime_type) or None on failure.
    """
    if not ELEVENLABS_API_KEY:
        logger.debug("ELEVENLABS_API_KEY not set; skipping TTS")
        return None

    url = f"https://api.elevenlabs.io/v1/text-to-speech/{ELEVENLABS_VOICE}"
    headers = {
        "xi-api-key": ELEVENLABS_API_KEY,
        "Content-Type": "application/json",
        "Accept": "audio/mpeg"
    }
    payload = {"text": text, "voice_settings": {}}

    try:
        async with httpx.AsyncClient(timeout=60) as client:
            resp = await client.post(url, json=payload, headers=headers)
            resp.raise_for_status()
            audio_bytes = resp.content
            mime = resp.headers.get("Content-Type", "audio/mpeg")
            b64 = base64.b64encode(audio_bytes).decode("ascii")
            logger.debug("Synthesized %d bytes, mime=%s", len(audio_bytes), mime)
            return b64, mime
    except httpx.HTTPStatusError as e:
        logger.exception("ElevenLabs HTTP error: %s - body: %s", e, e.response.text if e.response is not None else None)
    except Exception as e:
        logger.exception("ElevenLabs request failed: %s", e)

    return None
