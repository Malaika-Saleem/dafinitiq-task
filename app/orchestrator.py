from typing import Dict, Any, List, Optional
from .clients.llm import call_llm
import logging
from .clients.stt import transcribe_audio_base64
from .clients.tts import synthesize_text_to_base64
from .utils import load_menu, sanitize_for_tts, guardrail_check, compute_drift_score
from .db import get_session
from .models import CallSession
from datetime import datetime
import os

MENU = load_menu()

logger = logging.getLogger("app.orchestrator")

SYSTEM_PROMPT = "You are an AI voice ordering assistant for the restaurant. Answer only using the provided menu. Never invent items or prices. Keep replies short and spoken-language appropriate."

def start_call(caller_id: Optional[str] = None) -> str:
    session = get_session()
    cs = CallSession(caller_id=caller_id)
    session.add(cs)
    session.commit()
    session.refresh(cs)
    return cs.id

async def handle_audio_chunk(session_id: str, text: Optional[str] = None, audio_b64: Optional[str] = None) -> Dict[str, Any]:
    session = get_session()
    cs = session.get(CallSession, session_id)
    if cs is None:
        raise ValueError("session not found")

    # debug collection
    debug_info = {}
    try:
        debug_info['received'] = {'text_provided': bool(text), 'audio_provided': bool(audio_b64)}
    except Exception:
        pass

    # If audio provided and STT key present, transcribe; else use provided text
    transcript_text = text or ""
    if audio_b64 and not transcript_text:
        transcript_text = await transcribe_audio_base64(audio_b64)

    # append user turn
    turn = {"speaker": "user", "text": transcript_text, "timestamp": datetime.utcnow().isoformat()}
    cs.transcript.append(turn)

    # Build messages for LLM (Groq)
    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
    ]
    # add menu as system context (simplified)
    messages.append({"role": "system", "content": f"MENU:{MENU}"})
    # add history
    for t in cs.transcript:
        role = "user" if t["speaker"] == "user" else "assistant"
        messages.append({"role": role, "content": t["text"]})

    # call LLM
    try:
        # record which provider looks like will be used
        import os as _os
        debug_info['llm_env'] = {'LLM_PROVIDER': _os.environ.get('LLM_PROVIDER'), 'GROQ_API_KEY': bool(_os.environ.get('GROQ_API_KEY'))}
        # quick dev-mode simulation override to avoid external API failures
        force_sim = _os.environ.get('FORCE_SIMULATE', 'false').lower() in ('1','true','yes')
        if force_sim:
            last_user = next((m for m in reversed(messages) if m.get('role') == 'user'), {})
            content = last_user.get('content', 'Hello')
            llm_resp = {'content': f"(simulated) {content}"}
            debug_info['llm_response_raw'] = llm_resp
            debug_info['llm_forced_simulate'] = True
        else:
            llm_resp = await call_llm(SYSTEM_PROMPT, messages, MENU)
            debug_info['llm_response_raw'] = llm_resp
    except Exception as e:
        logger.exception("LLM call failed: %s", e)
        llm_resp = {"content": "Sorry, I'm having trouble right now."}
        debug_info['llm_exception'] = str(e)

    # Always log debug_info at debug level so server logs show details
    try:
        logger.debug("orchestrator debug: %s", debug_info)
    except Exception:
        pass
    # LLM response expected to contain content key
    reply_text = llm_resp.get("content") if isinstance(llm_resp, dict) else str(llm_resp)
    if not reply_text:
        reply_text = "Sorry, I didn't understand that."

    # Guardrails
    g = guardrail_check(reply_text, MENU)
    if not g["allowed"]:
        reply_text = "I'm sorry, I can't answer that. Please ask about items on our menu."

    reply_text = sanitize_for_tts(reply_text)

    # append assistant turn
    turn_assistant = {"speaker": "assistant", "text": reply_text, "timestamp": datetime.utcnow().isoformat()}
    cs.transcript.append(turn_assistant)

    # drift detection
    score = compute_drift_score(reply_text, MENU)
    cs.drift_log.append({"turn_index": len(cs.transcript)-1, "score": score, "corrected": False})
    # check last two scores
    recent = cs.drift_log[-2:]
    if len(recent) >= 2 and all(r["score"] < 0.5 for r in recent):
        cs.drift_detected = True
        # inject corrective system message
        correction = {"speaker": "system", "text": SYSTEM_PROMPT, "timestamp": datetime.utcnow().isoformat()}
        cs.transcript.append(correction)
        cs.drift_log.append({"turn_index": len(cs.transcript)-1, "score": 1.0, "corrected": True})

    session.add(cs)
    session.commit()

    # synthesize
    audio_result = None
    try:
        audio_result = await synthesize_text_to_base64(reply_text)
    except Exception as e:
        logger.exception("TTS failed: %s", e)
        debug_info['tts_exception'] = str(e)

    try:
        logger.debug("orchestrator after tts: %s", {'audio_result': bool(audio_result)})
    except Exception:
        pass

    audio_b64_out = None
    audio_mime = None
    if audio_result:
        audio_b64_out, audio_mime = audio_result

    # include debug info in dev mode
    show_debug = os.environ.get('SHOW_DEBUG', 'false').lower() in ('1','true','yes')
    out = {"reply_text": reply_text, "audio_base64": audio_b64_out, "audio_mime": audio_mime}
    if show_debug:
        out['debug'] = debug_info

    try:
        logger.debug("orchestrator response out: %s", {k: ('<redacted>' if k=='audio_base64' else v) for k,v in out.items()})
    except Exception:
        pass
    return out

async def end_call(session_id: str) -> Dict[str, Any]:
    session = get_session()
    cs = session.get(CallSession, session_id)
    if cs is None:
        raise ValueError("session not found")
    cs.ended_at = datetime.utcnow()

    # Build messages and ask LLM (Groq) to extract structured order JSON from the transcript
    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "system", "content": f"MENU:{MENU}"},
    ]
    for t in cs.transcript:
        role = "user" if t["speaker"] == "user" else "assistant"
        messages.append({"role": role, "content": t["text"]})

    # Instruction: return JSON only with keys: items: [{name, quantity, price}], total: number
    messages.append({"role": "user", "content": "Please extract the final order from the above conversation as JSON only with the schema {\"items\": [{\"name\": string, \"quantity\": int, \"price\": number}], \"total\": number}. Use prices from the menu. If no order detected, return {\"items\": [], \"total\": 0.0}."})

    # call LLM (Groq) to extract order
    llm_resp = await call_llm(SYSTEM_PROMPT, messages, MENU)
    resp_text = llm_resp.get("content") if isinstance(llm_resp, dict) else str(llm_resp)

    import json, re
    order = {"items": [], "total": 0.0}
    if resp_text:
        # try to extract JSON blob
        m = re.search(r"\{.*\}", resp_text, flags=re.S)
        if m:
            try:
                order = json.loads(m.group(0))
            except Exception:
                order = {"items": [], "total": 0.0}

    # fallback: naive regex if LLM failed
    if not order.get("items"):
        for t in cs.transcript:
            if t["speaker"] == "user":
                m = re.findall(r"(\d+)\s+(\w+)", t["text"].lower())
                for qty, name in m:
                    order["items"].append({"name": name, "quantity": int(qty)})

    cs.order_summary = order
    session.add(cs)
    session.commit()
    return {"order_summary": order}
