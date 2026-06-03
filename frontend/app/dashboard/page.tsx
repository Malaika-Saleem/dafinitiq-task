"use client"
import React, { useState } from 'react'
import DashboardCards from '../../components/dashboard/Cards'
import FilterBar from '../../components/dashboard/FilterBar'
import CallsTable from '../../components/dashboard/CallsTable'
import CallDetailSlideOver from '../../components/dashboard/CallDetailSlideOver'
import { mockCalls } from '../../lib/mock'
import AudioAgent from '../../components/dashboard/AudioAgent'

export default function DashboardPage(){
  const [selected, setSelected] = useState<string | null>(null)
  const [calls, setCalls] = useState(mockCalls)

  return (
    <div className="w-full max-w-6xl mx-auto">
      <header className="flex items-center justify-between py-6">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 bg-gradient-to-tr from-indigo-600 to-sky-400 rounded-full text-white flex items-center justify-center">RV</div>
          <h2 className="text-lg font-semibold">Dashboard</h2>
        </div>
        <div className="flex items-center gap-3">
          <div className="text-sm text-slate-600">Hello, Admin</div>
          <button className="px-3 py-2 bg-slate-100 rounded">Logout</button>
        </div>
      </header>

      <DashboardCards />
      <div className="mt-6">
        <FilterBar />
      </div>
      <div className="mt-4">
        <CallsTable calls={calls} onRowClick={(id)=>setSelected(id)} />
      </div>
      <CallDetailSlideOver callId={selected} onClose={()=>setSelected(null)} />
      <AudioAgent />
    </div>
  )
}
