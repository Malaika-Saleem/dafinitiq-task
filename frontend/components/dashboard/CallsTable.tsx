import React from 'react'
import { Call } from '../../lib/mock'

export default function CallsTable({calls,onRowClick}:{calls:Call[], onRowClick:(id:string)=>void}){
  if(!calls.length) return <div className="p-6 text-center text-slate-500">No calls found</div>
  return (
    <div className="bg-white rounded shadow overflow-hidden">
      <table className="w-full">
        <thead className="bg-slate-50 text-left text-sm text-slate-600">
          <tr>
            <th className="p-3">Call ID</th>
            <th className="p-3">Date</th>
            <th className="p-3">Duration</th>
            <th className="p-3">Caller</th>
            <th className="p-3">Status</th>
            <th className="p-3">Drift</th>
            <th className="p-3">Total</th>
          </tr>
        </thead>
        <tbody>
          {calls.map(c=> (
            <tr key={c.id} className="hover:bg-slate-50 cursor-pointer" onClick={()=>onRowClick(c.id)}>
              <td className="p-3">{c.id}</td>
              <td className="p-3">{c.date}</td>
              <td className="p-3">{c.duration}</td>
              <td className="p-3">{c.caller}</td>
              <td className="p-3"><span className={`px-2 py-1 rounded text-sm ${c.status==='Completed' ? 'bg-green-100 text-green-700' : 'bg-slate-100 text-slate-700'}`}>{c.status}</span></td>
              <td className="p-3">{c.drift ? <span className="px-2 py-1 rounded bg-amber-100 text-amber-800">Drift</span> : <span className="px-2 py-1 rounded bg-emerald-100 text-emerald-800">No Drift</span>}</td>
              <td className="p-3">{c.total}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}
