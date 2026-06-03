import React from 'react'
import { mockCallById } from '../../lib/mock'

export default function CallDetailSlideOver({callId,onClose}:{callId:string | null, onClose:()=>void}){
  if(!callId) return null
  const call = mockCallById(callId)
  if(!call) return null
  return (
    <div style={{position:'fixed',right:0,top:0,bottom:0,width:420}} className="bg-white shadow-lg p-4 overflow-auto">
      <div className="flex items-center justify-between">
        <h3 className="font-semibold">Call {call.id}</h3>
        <button onClick={onClose} className="text-slate-500">Close</button>
      </div>
      <div className="mt-4 space-y-3">
        <div><b>Caller:</b> {call.caller}</div>
        <div><b>Duration:</b> {call.duration}</div>
        <div><b>Start:</b> {call.start}</div>
        <div><b>End:</b> {call.end}</div>
        <div className="mt-4">
          <h4 className="font-semibold">Transcript</h4>
          <div className="mt-2 space-y-2">
            {call.transcript.map((m,i)=> (
              <div key={i} className={`p-2 rounded ${m.role==='user' ? 'bg-slate-50 text-slate-800' : 'bg-indigo-50 text-indigo-800'}`}>
                <div className="text-sm">{m.text}</div>
              </div>
            ))}
          </div>
        </div>
        <div>
          <h4 className="font-semibold">Order Summary</h4>
          <div className="mt-2">
            {call.order.map((it,i)=> (
              <div key={i} className="flex justify-between border-b py-2">
                <div>{it.name} x{it.qty}</div>
                <div>{it.price}</div>
              </div>
            ))}
            <div className="flex justify-between font-semibold mt-2"> <div>Total</div> <div>{call.total}</div></div>
          </div>
        </div>
      </div>
    </div>
  )
}
