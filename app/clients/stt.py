import os
import httpx
import base64
import logging
from typing import Optional

DEEPGRAM_API_KEY = os.environ.get("DEEPGRAM_API_KEY")

logger = logging.getLogger("app.clients.stt")


def _detect_mime(audio_bytes: bytes) -> str:
    """Simple header-based audio mime type detection."""
    if audio_bytes.startswith(b"RIFF") and b"WAVE" in audio_bytes[:12]:
        return "audio/wav"
    if audio_bytes.startswith(b"fLaC"):
        return "audio/flac"
    if audio_bytes.startswith(b"ID3") or (len(audio_bytes) > 1 and audio_bytes[0] == 0xFF):
        return "audio/mpeg"
    # MP4/M4A
    if b"ftyp" in audio_bytes[:64]:
        return "audio/mp4"
    # fallback
    return "application/octet-stream"


async def transcribe_audio_base64(audio_b64: str) -> str:
    """
    Decode base64 audio and send to Deepgram's REST /v1/listen endpoint.
    Returns the transcript text (or empty string on failure).
    """
    if not DEEPGRAM_API_KEY:
        logger.debug("DEEPGRAM_API_KEY not set; returning empty transcript")
        return ""

    try:
        audio_bytes = base64.b64decode(audio_b64)
    except Exception as e:
        logger.exception("Failed to decode base64 audio: %s", e)
        return ""

    mime = _detect_mime(audio_bytes)
    url = "https://api.deepgram.com/v1/listen"
    headers = {"Authorization": f"Token {DEEPGRAM_API_KEY}", "Content-Type": mime}
    params = {"punctuate": True, "language": "en-US"}
    logger.debug("Deepgram request: mime=%s bytes=%d", mime, len(audio_bytes))

    try:
        async with httpx.AsyncClient(timeout=60) as client:
            resp = await client.post(url, params=params, content=audio_bytes, headers=headers)
            try:
                resp.raise_for_status()
            except Exception as e:
                logger.exception("Deepgram non-200: %s body=%s", e, resp.text[:200])
                raise
            j = resp.json()
            # Deepgram response contains results -> channels -> [0] -> alternatives -> [0] -> transcript
            transcript = ""
            try:
                transcript = j.get("results", {}).get("channels", [])[0].get("alternatives", [])[0].get("transcript", "")
            except Exception:
                logger.debug("Unexpected Deepgram response shape: %s", j)
                transcript = ""
            logger.debug("Deepgram transcript: %s", transcript)
            return transcript
    except httpx.HTTPStatusError as e:
        logger.exception("Deepgram HTTP error: %s - body: %s", e, e.response.text if e.response is not None else None)
    except Exception as e:
        logger.exception("Deepgram request failed: %s", e)

    return ""
