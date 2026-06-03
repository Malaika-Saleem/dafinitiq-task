# Architecture: Dafinitiq Voice Ordering System

## Purpose
This document describes the system architecture, component responsibilities, data flow, integration points, and operational considerations for the Dafinitiq voice ordering system.

## High-level Components

- Backend (FastAPI)
  - Orchestrator: core pipeline coordinating STT → LLM → guardrails → TTS, session persistence, drift detection. (`app/orchestrator.py`)
  - Clients: service adapters for external APIs
    - Groq LLM client (`app/clients/groq.py`) — primary LLM interface with OpenAI-compatible fallbacks
    - Deepgram STT client (`app/clients/stt.py`)
    - ElevenLabs TTS client (`app/clients/tts.py`)
  - Auth: JWT + OTP, password hashing (`app/auth.py`)
  - Data model: `CallSession`, `User` via SQLModel/SQLAlchemy (`app/models.py`)
  - Utilities: menu loader, guardrails, drift scoring (`app/utils.py`)
  - Persistence: `sqlite` by default via SQLModel; `app/db.py` encapsulates engine/session

- Frontend (Next.js + TypeScript)
  - `AudioAgent` component records audio or accepts text and sends chunks to backend endpoints
  - Auth pages: sign-up, OTP, sign-in
  - Dashboard for staff to view calls and orders

- External Services
  - Groq (LLM) — conversational agent and structured-order extraction
  - Deepgram — speech-to-text
  - ElevenLabs — text-to-speech

## Data Flow (Call lifecycle)

1. Client requests `POST /webhook/call/start` → server creates `CallSession` and returns `session_id`.
2. Client sends audio/text to `POST /webhook/call/audio` with `session_id`.
   - If audio present and STT configured: server decodes base64 audio and calls Deepgram (`transcribe_audio_base64`) to produce `transcript_text`.
   - Otherwise uses provided `text` (frontend supports text fallback).
3. Orchestrator appends the user turn to session `transcript` (JSON array).
4. Orchestrator builds LLM messages: `SYSTEM_PROMPT` + `MENU` system context + transcript history.
5. LLM call via `call_llm()` (Groq client): returns normalized `{'content': text}`.
   - `FORCE_SIMULATE` can short-circuit to simulated replies for demos.
6. Reply is checked by `guardrail_check()` (off-topic keywords, length limit) — failing this replaces the reply with a safe message.
7. `sanitize_for_tts()` cleans text for speech.
8. Assistant turn appended to transcript; drift score computed (`compute_drift_score`), appended to `drift_log`.
   - If two consecutive recent scores < 0.5, set `drift_detected = True` and inject corrective `SYSTEM_PROMPT` into transcript.
9. TTS client invoked (`synthesize_text_to_base64`) to generate audio returned to client.
10. When call ends, `POST /webhook/call/end` prompts LLM to extract structured order JSON from transcript; fallback naive regex applies if LLM fails.

## Message / Payload Shapes

- LLM messages: list of `{role: system|user|assistant, content: string}`. `SYSTEM_PROMPT` is injected and `MENU` is sent as a system message to ground the model.
- Orchestrator response: `{ reply_text, audio_base64, audio_mime, debug? }`
- `CallSession.transcript`: array of `{ speaker: "user"|"assistant"|"system", text, timestamp }` stored as JSON.

## Guardrails and Scoring (detailed)

- Guardrail checks:
  - Off-topic keywords block responses (list in `_OFF_TOPIC_KW`).
  - Maximum reply length: 60 words.

- Drift score formula:
  - Base: 0.5
  - +0.4 if any menu item name appears in reply
  - +0.1 if ordering-related words present
  - -0.4 if any off-topic keyword appears
  - Clamped to [0.0, 1.0], rounded to 2 decimals.

- Drift trigger: if two most recent drift entries have score < 0.5, mark `drift_detected` and inject corrective system message.

## Error Handling & Fallback Strategy

- LLM:
  - If `GROQ_API_KEY` missing → simulated reply (local dev).
  - If `GROQ_API_URL` incorrect or provider returns errors → client tries a small set of candidate endpoints and OpenAI-compatible payloads; on total failure returns a simulated reply to avoid blocking the call.
  - `FORCE_SIMULATE=true` forces simulated replies for demos.
- STT:
  - If `DEEPGRAM_API_KEY` missing → `transcribe_audio_base64` returns empty string.
- TTS:
  - If `ELEVENLABS_API_KEY` missing or voice id invalid → TTS returns `None`. Frontend may fall back to browser SpeechSynthesis.

## Persistence & JSON Columns

- `CallSession.transcript`, `drift_log`, and `order_summary` are stored using SQLAlchemy `JSON` type (aliased `SA_JSON` in code).
- Important: in-place mutations of JSON fields are not automatically detected by the ORM; use `MutableDict`/mutable structures or reassign the value to ensure changes are persisted.

## Integration Contracts

- HTTP timeouts:
  - Groq: 30s
  - Deepgram / ElevenLabs: 60s
- Expected LLM response normalization: the Groq client extracts text from multiple possible shapes (`content`, `text`, `choices`, `outputs`) and returns `{'content': text}`.

## Operational Considerations

- Env variables (examples):
  - `GROQ_API_KEY`, `GROQ_API_URL`, `GROQ_MODEL`
  - `DEEPGRAM_API_KEY`
  - `ELEVENLABS_API_KEY`, `ELEVENLABS_VOICE_ID`
  - `JWT_SECRET`, `JWT_ALGORITHM`, `JWT_EXPIRE_SECONDS`
  - `FORCE_SIMULATE`, `SHOW_DEBUG`
- Logging: key loggers include `app.clients.groq`, `app.clients.stt`, `app.clients.tts`, and `app.orchestrator` with debug messages like `orchestrator debug:` and `orchestrator response out:`.

## Scaling & Deployment Notes

- For production:
  - Replace SQLite with managed DB (Postgres) for concurrency and JSONB support.
  - Use separate workers/processes for long-running or blocking operations (TTS/LLM) or use background task queue (Celery/RQ) to avoid blocking request threads.
  - Implement retries with exponential backoff for external API calls and circuit-breakers to avoid cascading failures.
  - Add request rate limiting (IP & user) and quotas for API usage.
  - Use containerization (Docker) and orchestrate with Kubernetes for horizontal scaling.

## Security

- Do not commit secrets: the repo now contains `.gitignore` and `.env.example` without secrets. Rotate any keys that were previously committed.
- Use a secrets manager in production.
- Enforce HTTPS and secure CORS, set secure cookie flags, and limit JWT lifetime and scopes.

## Diagrams (textual)

Sequence (simplified):

Client -> Backend (/start) -> returns session_id
Client -> Backend (/audio) -> (STT?) -> LLM -> Guardrails -> TTS -> Client

Component Map:
- Frontend (AudioAgent)
- FastAPI Orchestrator
- Clients: Deepgram, Groq, ElevenLabs
- DB: SQLModel on Postgres/SQLite

## Files & Entry Points
- `app/main.py` — app entry
- `app/orchestrator.py` — pipeline logic
- `app/clients/*` — external integrations
- `app/models.py` — data models
- `frontend/` — UI

## Next Steps
- Add architecture diagrams (Mermaid) and include them in this file or docs site.
- Implement background tasking for TTS/LLM calls and robust retry logic.
- Add CI pipeline with secret scanning and unit/integration tests.

---

File created. If you want this committed and pushed to GitHub, I can commit and push now.