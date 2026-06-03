# Dafinitiq Voice Ordering System — Project Report

## Overview

This repository implements a production-oriented AI voice ordering assistant for restaurants. The stack includes a Python FastAPI backend that orchestrates STT → LLM → TTS flows, session persistence with SQLModel/SQLite, JWT-based auth + OTP, and a Next.js frontend with a live `AudioAgent` for audio capture and optional text input.

## Architecture

- Backend: FastAPI, async `httpx` clients, SQLModel (SQLAlchemy) for persistence.
- Frontend: Next.js (App Router) + TypeScript + Tailwind.
- External services (optional): Groq (LLM), Deepgram (STT), ElevenLabs (TTS).

## File Map (important files)

- `app/main.py` — FastAPI app and routes.
- `app/orchestrator.py` — Core STT → LLM → guardrails → TTS pipeline and session management. [app/orchestrator.py](app/orchestrator.py#L1-L220)
- `app/clients/groq.py` — Groq/OpenAI-compatible LLM client with endpoint fallbacks and normalization. [app/clients/groq.py](app/clients/groq.py#L1-L240)
- `app/clients/stt.py` — Deepgram STT wrapper (base64 audio). [app/clients/stt.py](app/clients/stt.py#L1-L200)
- `app/clients/tts.py` — ElevenLabs TTS wrapper returning base64. [app/clients/tts.py](app/clients/tts.py#L1-L200)
- `app/clients/llm.py` — LLM dispatcher (delegates to Groq). [app/clients/llm.py](app/clients/llm.py)
- `app/utils.py` — Menu loader, guardrails, drift scoring. [app/utils.py](app/utils.py#L1-L220)
- `app/models.py` — `CallSession` and `User` definitions (JSON columns via SQLAlchemy JSON alias `SA_JSON`). [app/models.py](app/models.py#L1-L120)
- `app/auth.py` — OTP, JWT, password hashing. [app/auth.py](app/auth.py#L1-L140)
- `menu.json` — Canonical menu used to ground LLM responses.
- `frontend/` — Next.js app and components (notably `AudioAgent.tsx`).
- `.env.example` — environment variable template (no secrets). [.env.example](.env.example#L1-L60)

## Data Model

`CallSession` (stored JSON fields):
- `id` (UUID)
- `started_at`, `ended_at`
- `caller_id`
- `transcript` (JSON array of turns: `{speaker, text, timestamp}`)
- `order_summary` (JSON)
- `drift_detected` (bool)
- `drift_log` (JSON array: `{turn_index, score, corrected}`)

Notes: JSON columns use SQLAlchemy `JSON` (aliased as `SA_JSON`) which maps to vendor native JSON types. In-place mutations to JSON are not automatically detected by the ORM — use `MutableDict` or replace the whole value to ensure change tracking.

## Orchestrator: Flow & Behavior

1. `start_call(caller_id)`: creates `CallSession` and returns `session_id`.
2. `handle_audio_chunk(session_id, text?, audio_b64?)`:
   - If `audio_b64` present and `text` empty, call STT: `transcribe_audio_base64()`.
   - Append user turn to `transcript`.
   - Build LLM messages: system prompt + `MENU` system context + transcript history.
   - LLM call: `call_llm()` (Groq client). If `FORCE_SIMULATE=true`, return simulated reply.
   - Guardrails: run `guardrail_check(reply_text, MENU)` (see Guardrails section).
   - Sanitize text for TTS via `sanitize_for_tts()`.
   - Append assistant turn, compute drift score and update drift log.
   - If last two drift scores both < 0.5, mark drift detected and inject corrective `SYSTEM_PROMPT` with an auto-correct entry.
   - Synthesize audio via `synthesize_text_to_base64()`.
   - Return `{reply_text, audio_base64, audio_mime}` and `debug` when `SHOW_DEBUG=true`.
3. `end_call(session_id)`: builds an instruction asking the LLM to extract a structured order JSON and attempts to parse it; if LLM fails, a naive regex fallback is attempted.

## LLM (Groq) Client Details

- Env vars: `GROQ_API_KEY`, `GROQ_API_URL` (preferred), `GROQ_MODEL`.
- Behavior:
  - If `GROQ_API_KEY` missing → simulated reply for local testing.
  - The client first attempts a provider-native payload: `{"system": system_prompt, "messages": messages, "menu": menu_json}`.
  - If that fails, it tries OpenAI-compatible chat payload: `{"model": GROQ_MODEL, "messages": [...], "temperature":0.3, "max_tokens":512}`.
  - Candidate URLs tried (if `GROQ_API_URL` unset):
    - `https://api.groq.com/v1/chat/completions`
    - `https://api.groq.dev/v1/chat/completions`
    - `https://api.groq.dev/v1/generate`
    - `https://api.groq.ai/v1/chat/completions`
  - On repeated failures, returns a simulated reply containing a short error indicator to allow the orchestrator to proceed.
  - Response normalization supports multiple shapes: `{'content':..}`, `{'text':..}`, `choices[0].text`, or outputs->content structures.

## STT (Deepgram) Details

- Env: `DEEPGRAM_API_KEY`.
- Request: POST to `https://api.deepgram.com/v1/listen` with raw audio bytes, headers `Authorization: Token <key>` and content-type detected from audio bytes.
- Query params: `punctuate=true`, `language=en-US`.
- Expected response shape: `results.channels[0].alternatives[0].transcript`.
- Timeout: 60s. Returns `""` on failure.

## TTS (ElevenLabs) Details

- Env: `ELEVENLABS_API_KEY`, `ELEVENLABS_VOICE_ID` (defaults to `alloy`).
- Endpoint: `POST https://api.elevenlabs.io/v1/text-to-speech/{voice_id}` with `xi-api-key` header.
- Returns base64-encoded audio and MIME type (e.g., `audio/mpeg`).
- Timeout: 60s. If no TTS key or voice not found, `synthesize_text_to_base64()` returns `None` and orchestrator may use browser speech fallback for the frontend.

## Guardrails & Drift Scoring (Formulas)

- Guardrails (`guardrail_check`):
  - Off-topic keywords list (`_OFF_TOPIC_KW`) — any presence denies the response.
  - Maximum length: 60 words — responses longer than this are rejected.

- Drift scoring (`compute_drift_score`):
  - Start: base score = 0.5
  - If a menu item is mentioned: +0.4
  - If ordering-related words are present: +0.1
  - If any off-topic keyword is present: -0.4
  - Clamp to [0.0, 1.0], round to 2 decimals.

Mathematically:

$$
score = \mathrm{clamp}_{[0,1]}\big(0.5 + 0.4\cdot I + 0.1\cdot W - 0.4\cdot O\big)
$$

Where:
- $I \in \{0,1\}$: any menu item mentioned;
- $W \in \{0,1\}$: ordering words present;
- $O \in \{0,1\}$: off-topic keyword present.

- Drift detection trigger: if the two most recent drift scores are both $<0.5$, the system flags drift and injects a corrective system message; the corrective entry is logged with `score = 1.0` and `corrected = True`.

## Environment Variables (list)

- Core:
  - `APP_HOST` (default `0.0.0.0`)
  - `APP_PORT` (default `8000`)
  - `DATABASE_URL` (default `sqlite:///./voice_agent.db`)
- Secrets / APIs:
  - `GROQ_API_KEY`, `GROQ_API_URL`, `GROQ_MODEL`
  - `DEEPGRAM_API_KEY`
  - `ELEVENLABS_API_KEY`, `ELEVENLABS_VOICE_ID`
  - `JWT_SECRET`, `JWT_ALGORITHM`, `JWT_EXPIRE_SECONDS`
- Feature toggles & debug:
  - `FORCE_SIMULATE` — force simulated LLM responses (for demos)
  - `SHOW_DEBUG` — include `debug` object in orchestrator response
  - `SHOW_DESKTOP_OTP` — show Windows notification when sending OTPs
- Frontend:
  - `NEXT_PUBLIC_API_BASE` — backend base URL for the frontend.

## Timeouts & Limits

- HTTP timeouts:
  - LLM (Groq): 30s
  - STT/TTS: 60s
- Guardrails: Max response length 60 words
- Drift sensitivity: Two consecutive scores < 0.5 trigger corrective action

## Request/Response Examples

- Start call (POST `/webhook/call/start`):
```json
{ "caller_id": "test" }
```
Response: `{ "session_id": "<uuid>" }`

- Send text/audio chunk (POST `/webhook/call/audio`):
Request body example:
```json
{ "session_id": "<uuid>", "text": "hello whats the menu?" }
```
Response example:
```json
{
  "reply_text": "We have bagels and sandwiches...",
  "audio_base64": "<base64 or null>",
  "audio_mime": "audio/mpeg",
  "debug": { /* present only if SHOW_DEBUG=true */ }
}
```

- End call (POST `/webhook/call/end`) returns order extraction:
```json
{ "order_summary": {"items": [{"name":"plain bagel","quantity":2,"price":2.5}], "total": 5.0} }
```

## Debugging Tips

- Enable `SHOW_DEBUG=true` to get `debug_info` containing `llm_response_raw`, `llm_env`, `tts_exception`, etc.
- Check logs for `app.clients.groq` to see which endpoints and payloads were tried.
- If LLM returns generic failure, either set `FORCE_SIMULATE=true` for demos or ensure `GROQ_API_KEY` & correct `GROQ_API_URL` are set in the same shell running uvicorn.
- For ElevenLabs TTS 404 `voice_not_found`, set `ELEVENLABS_VOICE_ID` to a supported voice.

## Security Recommendations

- Rotate any API keys previously embedded in commits (if any were pushed) immediately.
- Use a secrets manager or environment-specific secret injection rather than `.env` files in CI.
- Add GitHub Actions secret-scan or pre-commit hooks to block accidental secret commits.
- Set `JWT_SECRET` to a long, high-entropy secret in production; do not use default.
- Limit CORS in production to known origins and enforce HTTPS.

## Test & Run (quick)

Local run (PowerShell):
```powershell
$env:GROQ_API_KEY = '<your_key>'
$env:GROQ_API_URL = 'https://api.groq.com/openai/v1'
$env:ELEVENLABS_API_KEY = '<your_key>'
$env:DEEPGRAM_API_KEY = '<your_key>'
$env:SHOW_DEBUG = 'true'
Remove-Item Env:FORCE_SIMULATE -ErrorAction SilentlyContinue
& .\.venv\Scripts\Activate.ps1
uvicorn app.main:app --reload --port 8000
```

Frontend:
```bash
cd frontend
npm install
npm run dev
```

API smoke test (PowerShell):
```powershell
$start = Invoke-RestMethod -Uri http://127.0.0.1:8000/webhook/call/start -Method POST -ContentType 'application/json' -Body (@{caller_id='test'} | ConvertTo-Json)
$sid = $start.session_id
$body = @{session_id=$sid; text='hello whats the menu?'} | ConvertTo-Json
Invoke-RestMethod -Uri http://127.0.0.1:8000/webhook/call/audio -Method POST -ContentType 'application/json' -Body $body | ConvertTo-Json -Depth 5
```

## Next Steps & Improvements

- Add unit tests for `compute_drift_score`, `guardrail_check`, and `end_call` extractor.
- Improve change-detection for JSON columns (use `MutableDict` or `MutableList` wrappers).
- Add rate-limiting and retry/backoff strategies for external APIs.
- Add CI checks to block secrets and run linters/tests.
- Add a dashboard debug panel to display realtime `debug` objects for each call.

---

_Report generated automatically. For any additions or format preferences (PDF, slide deck, or including full example logs), tell me and I'll produce the desired artifact._
