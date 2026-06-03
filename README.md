Restaurant Voice Agent - Technical Assessment

This repository implements a FastAPI backend for the Restaurant SaaS Voice Agent assessment.

Overview
- FastAPI backend implementing orchestrator endpoints, auth (OTP + JWT), call/session persistence, guardrails and drift detection.
- Menu data must be placed at `menu.json` in the repo root (already present).

Quickstart (local testing)
1. Create a Python 3.10+ virtualenv and install dependencies:

```bash
python -m venv .venv
source .venv/Scripts/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

2. Copy `.env.example` to `.env` and fill keys (optional for real STT/TTS/Groq).

3. Start the app:

```bash
uvicorn app.main:app --reload --port 8000
```

API Notes
- POST /webhook/call/start -> creates session, returns `session_id`.
- POST /webhook/call/audio -> accepts JSON {session_id, text} for local testing (or base64 audio). Returns agent reply and optional base64 audio.
- POST /webhook/call/end -> finalises call and persists order.
- Auth endpoints at /api/auth/* and calls endpoints at /api/calls* (JWT required).

Testing locally
- For rapid testing, send transcript text in `/webhook/call/audio` instead of audio. The orchestrator supports pluggable STT/TTS when API keys are provided.

Menu path
- The server loads `menu.json` from the repository root at startup. Ensure it exists.

Example cURL flow

1) Start a call

```bash
curl -X POST http://localhost:8000/webhook/call/start -H "Content-Type: application/json" -d '{"caller_id":"+15551234"}'
```

Response: `{ "session_id": "..." }`

2) Send a text chunk (local testing)

```bash
curl -X POST http://localhost:8000/webhook/call/audio -H "Content-Type: application/json" -d '{"session_id":"<SESSION_ID>","text":"Hi, what are your specials today?"}'
```

3) End the call

```bash
curl -X POST http://localhost:8000/webhook/call/end -H "Content-Type: application/json" -d '{"session_id":"<SESSION_ID>"}'
```

Frontend (React + Vite)

The repo includes a minimal TypeScript React frontend under `frontend/`. To run it:

```bash
cd frontend
npm install
npm run dev
```

Open the frontend at `http://localhost:5173`. By default it talks to the backend at `http://localhost:8000`.


