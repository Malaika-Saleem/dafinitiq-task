import os
from fastapi import FastAPI, HTTPException, Depends, Body
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
from .db import init_db, get_session
from .orchestrator import start_call, handle_audio_chunk, end_call
from .schemas import AudioChunk, EndCallRequest, AuthSignup, AuthLogin
from .auth import create_user, generate_otp, send_otp, find_user_by_email, verify_password, create_access_token
from sqlmodel import select
from .models import User, CallSession
import os

app = FastAPI(title="Restaurant Voice Agent")

app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_methods=["*"],
        allow_headers=["*"],
)


@app.on_event("startup")
def on_startup():
    init_db()
    import logging
    logging.basicConfig(level=logging.INFO)


@app.post("/webhook/call/start")
def api_start_call(payload: dict = Body(...)):
        caller = payload.get("caller_id")
        sid = start_call(caller)
        return {"session_id": sid}


@app.post("/webhook/call/audio")
async def api_audio(chunk: AudioChunk):
        try:
                out = await handle_audio_chunk(chunk.session_id, text=chunk.text, audio_b64=chunk.audio_base64)
                return out
        except Exception as e:
                raise HTTPException(status_code=400, detail=str(e))


@app.post("/webhook/call/end")
async def api_end(req: EndCallRequest):
    try:
        out = await end_call(req.session_id)
        return out
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.post("/api/auth/signup")
def api_signup(payload: AuthSignup):
        existing = find_user_by_email(payload.email)
        if existing:
                raise HTTPException(status_code=400, detail="email exists")
        user = create_user(payload.email, payload.display_name, payload.password)
        otp = generate_otp()
        # user was created/committed in a different session inside create_user();
        # re-query in a new session to avoid attaching the same object across sessions.
        from datetime import datetime, timedelta
        session = get_session()
        q = select(User).where(User.email == payload.email)
        user_db = session.exec(q).first()
        user_db.otp = otp
        user_db.otp_expires = datetime.utcnow() + timedelta(minutes=15)
        session.add(user_db)
        session.commit()
        send_otp(user_db.email, otp)
        # In development, optionally return the OTP in the response for convenience.
        show_otp = os.environ.get("SHOW_OTP", "true").lower() in ("1", "true", "yes")
        if show_otp:
            return {"message": "otp_sent", "otp": otp}
        return {"message": "otp_sent"}


@app.post("/api/auth/verify-otp")
def api_verify_otp(payload: dict = Body(...)):
        email = payload.get("email")
        otp = payload.get("otp")
        session = get_session()
        q = select(User).where(User.email == email)
        user = session.exec(q).first()
        if not user or user.otp != otp:
                raise HTTPException(status_code=400, detail="invalid")
        user.is_active = True
        user.otp = None
        user.otp_expires = None
        session.add(user)
        session.commit()
        return {"message": "verified"}


@app.post("/api/auth/login")
def api_login(payload: AuthLogin):
        session = get_session()
        q = select(User).where(User.email == payload.email)
        user = session.exec(q).first()
        if not user or not verify_password(payload.password, user.hashed_password):
                raise HTTPException(status_code=401, detail="invalid credentials")
        token = create_access_token(str(user.id))
        return {"access_token": token}


@app.post("/api/auth/forgot-password")
def api_forgot_password(payload: dict = Body(...)):
    email = payload.get("email")
    session = get_session()
    q = select(User).where(User.email == email)
    user = session.exec(q).first()
    if not user:
        raise HTTPException(status_code=404, detail="user not found")
    otp = generate_otp()
    user.otp = otp
    from datetime import datetime, timedelta
    user.otp_expires = datetime.utcnow() + timedelta(minutes=15)
    session.add(user)
    session.commit()
    send_otp(user.email, otp)
    return {"message": "otp_sent"}


@app.post("/api/auth/reset-password")
def api_reset_password(payload: dict = Body(...)):
    email = payload.get("email")
    otp = payload.get("otp")
    new_password = payload.get("new_password")
    session = get_session()
    q = select(User).where(User.email == email)
    user = session.exec(q).first()
    if not user or user.otp != otp:
        raise HTTPException(status_code=400, detail="invalid")
    from .auth import hash_password
    user.hashed_password = hash_password(new_password)
    user.otp = None
    user.otp_expires = None
    session.add(user)
    session.commit()
    return {"message": "password_reset"}


@app.get("/api/calls")
def list_calls():
        session = get_session()
        q = select(CallSession).order_by(CallSession.started_at.desc())
        res = session.exec(q).all()
        return res


@app.get("/api/calls/{call_id}")
def get_call(call_id: str):
        session = get_session()
        cs = session.get(CallSession, call_id)
        if not cs:
                raise HTTPException(status_code=404, detail="not found")
        return cs


@app.get("/", response_class=HTMLResponse)
def root_ui():
        html = """
        <!doctype html>
        <html>
        <head>
            <meta charset="utf-8" />
            <title>Voice Agent Dashboard (Dev)</title>
            <style>body{font-family:Arial;padding:16px}input,button,textarea{margin:4px 0;padding:8px;width:100%}#container{max-width:900px;margin:auto}</style>
        </head>
        <body>
        <div id="container">
            <h2>Voice Agent - Dev Dashboard</h2>
            <section>
                <h3>Auth</h3>
                <div>
                    <input id="su_email" placeholder="email" />
                    <input id="su_name" placeholder="display name" />
                    <input id="su_pass" type="password" placeholder="password" />
                    <button onclick="signup()">Sign Up (send OTP to console)</button>
                </div>
                <div>
                    <input id="otp_email" placeholder="email for OTP verify" />
                    <input id="otp_code" placeholder="otp code" />
                    <button onclick="verifyOtp()">Verify OTP</button>
                </div>
                <div>
                    <input id="li_email" placeholder="email" />
                    <input id="li_pass" type="password" placeholder="password" />
                    <button onclick="login()">Login</button>
                </div>
                <div>Token: <span id="token">(none)</span></div>
            </section>

            <section>
                <h3>Call Controls</h3>
                <div>
                    <button onclick="startCall()">Start Call</button>
                    <div>Session: <span id="session_id">(none)</span></div>
                </div>
                <div>
                    <textarea id="user_text" rows="3" placeholder="Type caller text here (for testing)"></textarea>
                    <button onclick="sendChunk()">Send Chunk (text)</button>
                </div>
                <div>
                    <button onclick="endCall()">End Call</button>
                </div>
                <div id="last_reply"></div>
            </section>

            <section>
                <h3>Calls</h3>
                <button onclick="listCalls()">Refresh Calls</button>
                <div id="calls_list"></div>
            </section>
        </div>

        <script>
        function setToken(t){
            if(t){ localStorage.setItem('va_token', t); document.getElementById('token').innerText = t; }
        }
        document.getElementById('token').innerText = localStorage.getItem('va_token') || '(none)';

        async function signup(){
            const email=document.getElementById('su_email').value; const name=document.getElementById('su_name').value; const pass=document.getElementById('su_pass').value;
            const r=await fetch('/api/auth/signup',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({email,display_name:name,password:pass})});
            alert((await r.json()).message || JSON.stringify(await r.json()));
        }
        async function verifyOtp(){
            const email=document.getElementById('otp_email').value; const otp=document.getElementById('otp_code').value;
            const r=await fetch('/api/auth/verify-otp',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({email,otp})});
            alert((await r.json()).message || JSON.stringify(await r.json()));
        }
        async function login(){
            const email=document.getElementById('li_email').value; const password=document.getElementById('li_pass').value;
            const r=await fetch('/api/auth/login',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({email,password})});
            const j=await r.json(); if(j.access_token){ setToken(j.access_token); alert('logged in'); } else alert(JSON.stringify(j));
        }

        async function startCall(){
            const r=await fetch('/webhook/call/start',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({caller_id:'web-ui'})});
            const j=await r.json(); document.getElementById('session_id').innerText=j.session_id; alert('started');
        }
        async function sendChunk(){
            const session_id=document.getElementById('session_id').innerText; const text=document.getElementById('user_text').value;
            if(!session_id || session_id==='(none)'){ alert('start a session first'); return; }
            const r=await fetch('/webhook/call/audio',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({session_id,text})});
            const j=await r.json(); document.getElementById('last_reply').innerText = j.reply_text || JSON.stringify(j);
        }
        async function endCall(){
            const session_id=document.getElementById('session_id').innerText;
            const r=await fetch('/webhook/call/end',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({session_id})});
            const j=await r.json(); alert('ended'); document.getElementById('last_reply').innerText = 'Order: '+JSON.stringify(j.order_summary);
        }

        async function listCalls(){
            const r=await fetch('/api/calls'); const j=await r.json();
            const el=document.getElementById('calls_list'); el.innerHTML=''; j.forEach(c=>{ const d=document.createElement('div'); d.style.border='1px solid #ccc'; d.style.padding='8px'; d.style.margin='6px 0'; d.innerHTML=`<b>${c.id}</b> - ${c.started_at} - <button onclick="viewCall('${c.id}')">View</button>`; el.appendChild(d); });
        }
        async function viewCall(id){ const r=await fetch('/api/calls/'+id); const j=await r.json(); alert(JSON.stringify(j, null, 2)); }
        </script>
        </body>
        </html>
        """
        return html
