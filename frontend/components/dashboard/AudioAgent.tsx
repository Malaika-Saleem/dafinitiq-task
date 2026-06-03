"use client"
import React, { useEffect, useRef, useState } from 'react'

const API = process.env.NEXT_PUBLIC_API_BASE || ''

function arrayBufferToBase64(buffer: ArrayBuffer){
  let binary = ''
  const bytes = new Uint8Array(buffer)
  const len = bytes.byteLength
  for(let i=0;i<len;i++) binary += String.fromCharCode(bytes[i])
  return btoa(binary)
}

function base64ToUint8Array(base64: string){
  const binary = atob(base64)
  const len = binary.length
  const bytes = new Uint8Array(len)
  for(let i=0;i<len;i++) bytes[i] = binary.charCodeAt(i)
  return bytes
}

export default function AudioAgent(){
  const [sessionId, setSessionId] = useState<string | null>(null)
  const [recording, setRecording] = useState(false)
  const [textIn, setTextIn] = useState('')
  const [messages, setMessages] = useState<string[]>([])
  const mediaRecorderRef = useRef<MediaRecorder | null>(null)

  useEffect(()=>{
    return ()=>{ if(mediaRecorderRef.current && mediaRecorderRef.current.state !== 'inactive') mediaRecorderRef.current.stop() }
  },[])

  const startCall = async ()=>{
    try{
      const res = await fetch(API + '/webhook/call/start',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({caller_id:'dashboard'})})
      const j = await res.json()
      if(!res.ok) return alert(JSON.stringify(j))
      setSessionId(j.session_id)
      setMessages(m=>[...m, 'Session started: '+j.session_id])
    }catch(err:any){ alert('Network error: '+(err?.message||err)) }
  }

  const endCall = async ()=>{
    if(!sessionId) return alert('no session')
    try{
      const res = await fetch(API + '/webhook/call/end',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({session_id:sessionId})})
      const j = await res.json()
      if(!res.ok) return alert(JSON.stringify(j))
      setMessages(m=>[...m, 'Call ended. Order: '+JSON.stringify(j.order_summary)])
      setSessionId(null)
    }catch(err:any){ alert('Network error: '+(err?.message||err)) }
  }

  const startRecording = async ()=>{
    if(!sessionId) return alert('Start a session first')
    if(!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) return alert('getUserMedia not supported')
    try{
      const stream = await navigator.mediaDevices.getUserMedia({audio:true})
      const mr = new MediaRecorder(stream, {mimeType: 'audio/webm'})
      mediaRecorderRef.current = mr
      mr.ondataavailable = async (ev)=>{
        if(!ev.data || ev.data.size===0) return
        const buf = await ev.data.arrayBuffer()
        const b64 = arrayBufferToBase64(buf)
        // send chunk
        try{
          const res = await fetch(API + '/webhook/call/audio',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({session_id:sessionId, audio_base64: b64})})
          const j = await res.json()
          if(!res.ok){ console.warn('server error', j); return }
          if(j.reply_text) setMessages(m=>[...m, 'Assistant: '+j.reply_text])
          if(j.audio_base64 && j.audio_mime){
            const bytes = base64ToUint8Array(j.audio_base64)
            const blob = new Blob([bytes], {type: j.audio_mime || 'audio/mpeg'})
            const url = URL.createObjectURL(blob)
            const a = new Audio(url)
            a.play().catch(e=>console.warn('play error',e))
          } else if(j.reply_text){
            // Fallback: use browser TTS if backend didn't return audio
            try{
              const u = new SpeechSynthesisUtterance(j.reply_text)
              window.speechSynthesis.cancel()
              window.speechSynthesis.speak(u)
            }catch(e){ console.debug('SpeechSynthesis not available', e) }
          }
        }catch(err:any){ console.error('send chunk error', err) }
      }
      mr.start(1000)
      setRecording(true)
      setMessages(m=>[...m,'Recording...'])
    }catch(err:any){ alert('microphone error: '+(err?.message||err)) }
  }

  const stopRecording = ()=>{
    const mr = mediaRecorderRef.current
    if(!mr) return
    try{ mr.stop() }catch(e){}
    const tracks = (mr as any).stream?.getTracks?.() || []
    tracks.forEach((t:any)=>t.stop())
    mediaRecorderRef.current = null
    setRecording(false)
    setMessages(m=>[...m,'Recording stopped'])
  }

  return (
    <div className="p-4 border rounded mt-6">
      <h3 className="font-semibold mb-2">Live Audio Agent</h3>
      <div className="flex gap-2 mb-3">
        <button className="px-3 py-2 bg-green-600 text-white rounded" onClick={startCall}>Start Session</button>
        <button className="px-3 py-2 bg-red-600 text-white rounded" onClick={endCall}>End Session</button>
        {!recording?
          <button className="px-3 py-2 bg-indigo-600 text-white rounded" onClick={startRecording}>Start Recording</button>
          : <button className="px-3 py-2 bg-yellow-500 text-white rounded" onClick={stopRecording}>Stop Recording</button>
        }
      </div>
      <div className="flex gap-2 mb-3">
        <input value={textIn} onChange={(e)=>setTextIn(e.target.value)} placeholder="Type text input..." className="flex-1 p-2 border rounded" />
        <button className="px-3 py-2 bg-blue-600 text-white rounded" onClick={async ()=>{
          if(!sessionId) return alert('Start a session first')
          if(!textIn) return
          setMessages(m=>[...m, 'You: '+textIn])
          try{
            const res = await fetch(API + '/webhook/call/audio',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({session_id:sessionId, text: textIn})})
            const j = await res.json()
            if(!res.ok) return alert(JSON.stringify(j))
            if(j.reply_text) setMessages(m=>[...m, 'Assistant: '+j.reply_text])
              if(j.audio_base64 && j.audio_mime){
                const bytes = base64ToUint8Array(j.audio_base64)
                const blob = new Blob([bytes], {type: j.audio_mime || 'audio/mpeg'})
                const url = URL.createObjectURL(blob)
                const a = new Audio(url)
                a.play().catch(e=>console.warn('play error',e))
              } else if(j.reply_text){
                try{
                  const u = new SpeechSynthesisUtterance(j.reply_text)
                  window.speechSynthesis.cancel()
                  window.speechSynthesis.speak(u)
                }catch(e){ console.debug('SpeechSynthesis not available', e) }
              }
          }catch(err:any){ console.error('send text error', err); alert('Network error') }
          setTextIn('')
        }}>Send</button>
      </div>
      <div className="text-sm text-slate-700">
        <div>Session: {sessionId || '(none)'}</div>
        <div className="mt-2">Messages:</div>
        <div className="mt-1 space-y-1 max-h-48 overflow-auto">
          {messages.map((m,i)=>(<div key={i} className="text-xs">{m}</div>))}
        </div>
      </div>
    </div>
  )
}
