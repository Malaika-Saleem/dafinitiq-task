import React, { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'

const API = import.meta.env.VITE_API_BASE || 'http://localhost:8000'

export default function Dashboard(){
  const [sessionId, setSessionId] = useState('')
  const [text, setText] = useState('')
  const [lastReply, setLastReply] = useState('')
  const [calls, setCalls] = useState<any[]>([])

  async function start(){
    const r = await fetch(`${API}/webhook/call/start`,{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({caller_id:'web-frontend'})})
    const j = await r.json(); setSessionId(j.session_id)
  }
  async function send(){
    if(!sessionId) return alert('start session')
    const r = await fetch(`${API}/webhook/call/audio`,{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({session_id:sessionId,text})})
    const j = await r.json();
    setLastReply(j.reply_text || JSON.stringify(j))
    // if audio present, play it
    if(j.audio_base64){
      try{
        const mime = j.audio_mime || 'audio/mpeg'
        const byteChars = atob(j.audio_base64)
        const byteNumbers = new Array(byteChars.length)
        for (let i = 0; i < byteChars.length; i++) byteNumbers[i] = byteChars.charCodeAt(i)
        const byteArray = new Uint8Array(byteNumbers)
        const blob = new Blob([byteArray], {type: mime})
        const url = URL.createObjectURL(blob)
        const audio = new Audio(url)
        audio.play()
      }catch(e){
        console.error('Failed to play audio', e)
      }
    }
  }
  async function end(){
    if(!sessionId) return
    const r = await fetch(`${API}/webhook/call/end`,{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({session_id:sessionId})})
    const j = await r.json(); alert('Ended - order: '+JSON.stringify(j.order_summary))
  }
  const navigate = useNavigate()
  async function fetchCalls(){
    const r = await fetch(`${API}/api/calls`); const j = await r.json(); setCalls(j)
  }

  useEffect(()=>{ fetchCalls() }, [])

  return (
    <div className="card">
      <h2>Dashboard</h2>
      <div>
        <button onClick={start}>Start Call</button>
        <div>Session: {sessionId || '(none)'}</div>
      </div>
      <textarea rows={4} value={text} onChange={e=>setText(e.target.value)} placeholder="Caller text for testing" />
      <button onClick={send}>Send Chunk</button>
      <button onClick={end}>End Call</button>
      <div className="reply">Reply: {lastReply}</div>

      <h3>Calls</h3>
      <button onClick={fetchCalls}>Refresh</button>
      <div>
        {calls.map(c=> (
          <div key={c.id} className="call">
            <div><b>{c.id}</b></div>
            <div>Started: {c.started_at}</div>
            <div><button onClick={()=>navigate(`/dashboard/call/${c.id}`)}>View</button></div>
          </div>
        ))}
      </div>
    </div>
  )
}
