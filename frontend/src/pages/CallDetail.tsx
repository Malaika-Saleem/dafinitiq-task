import React, { useEffect, useState } from 'react'
import { useParams, Link } from 'react-router-dom'

const API = import.meta.env.VITE_API_BASE || 'http://localhost:8000'

export default function CallDetail(){
  const { id } = useParams()
  const [call, setCall] = useState<any>(null)

  useEffect(()=>{
    if(!id) return
    fetch(`${API}/api/calls/${id}`).then(r=>r.json()).then(setCall)
  }, [id])

  if(!call) return <div className="card">Loading...</div>

  return (
    <div className="card">
      <h2>Call Detail</h2>
      <div><b>ID:</b> {call.id}</div>
      <div><b>Started:</b> {call.started_at}</div>
      <div><b>Ended:</b> {call.ended_at}</div>
      <div><b>Caller:</b> {call.caller_id}</div>
      <h3>Transcript</h3>
      <div style={{whiteSpace:'pre-wrap'}}>{JSON.stringify(call.transcript, null, 2)}</div>
      <h3>Order Summary</h3>
      <pre>{JSON.stringify(call.order_summary, null, 2)}</pre>
      <Link to="/dashboard">Back</Link>
    </div>
  )
}
